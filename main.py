import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import re

# Konfiguracja połączenia z bazą danych PostgreSQL
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'szymon',
    'host': 'localhost',
    'port': 5432
}

class GymApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja Kliencka - Siłownia")
        self.conn = None
        self.cursor = None

        # Wybór tabeli
        self.table_var = tk.StringVar()
        self.table_var.trace('w', self.update_table_view)
        self.tables = [
            "Klienci", "Pracownicy", "Czlonkostwo", "Instruktor", "Biurowy",
            "Zajecia", "Sprzet", "Rezerwacja_sprzetu", "Platnosc", "Wydarzenia",
            "Anulowanie_czlonkostwa", "Placowki", "Ocena_instruktorow", "Grafik_pracownikow"
        ]

        self.create_widgets()

    def connect_to_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            messagebox.showinfo("Połączenie", "Połączono z bazą danych")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się połączyć z bazą danych: {e}")

    def create_widgets(self):
        # Dropdown wyboru tabeli
        ttk.Label(self.root, text="Wybierz tabelę:").pack()
        table_menu = ttk.Combobox(self.root, textvariable=self.table_var, values=self.tables, state="readonly")
        table_menu.pack()

        # Tabela danych
        self.tree = ttk.Treeview(self.root, columns=(), show="headings")
        self.tree.pack(expand=True, fill="both")

        # Przyciski do operacji CRUD
        button_frame = tk.Frame(self.root)
        button_frame.pack()

        ttk.Button(button_frame, text="Dodaj", command=self.add_record).pack(side="left")
        ttk.Button(button_frame, text="Edytuj", command=self.edit_record).pack(side="left")
        ttk.Button(button_frame, text="Usuń", command=self.delete_record).pack(side="left")

    def update_table_view(self, *args):
        table_name = self.table_var.get()
        if not table_name:
            return

        try:
            self.cursor.execute(f"SELECT * FROM {table_name};")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]

            # Ustawienie nagłówków w Treeview
            self.tree["columns"] = columns
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)

            # Wyczyść istniejące dane
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Wstaw nowe dane
            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się załadować danych: {e}")

    def add_record(self):
        self.show_form("Dodaj rekord")

    def edit_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ostrzeżenie", "Wybierz rekord do edycji")
            return

        row_data = self.tree.item(selected_item, "values")
        self.show_form("Edytuj rekord", row_data)

    def delete_record(self):
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("Ostrzeżenie", "Wybierz rekord do usunięcia")
            return

        table_name = self.table_var.get()
        row_data = self.tree.item(selected_item, "values")
        primary_key = row_data[0]  # Zakładamy, że pierwsza kolumna to klucz główny
        self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        columns = [desc[0] for desc in self.cursor.description]

        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć rekord?") == "no":
            return
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {columns[0]} = %s;", (primary_key,))
            self.conn.commit()
            self.update_table_view()
            messagebox.showinfo("Sukces", "Rekord został usunięty")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się usunąć rekordu: {e}")

    def show_form(self, title, data=None):
        form = tk.Toplevel(self.root)
        form.title(title)

        table_name = self.table_var.get()
        self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        columns = [desc[0] for desc in self.cursor.description]

        entries = {}
        count = 0
        for i, column in enumerate(columns):
            if count==0 and table_name != "Instruktor" and table_name != "Biurowy":
                count+=1
                continue

            # Sprawdzamy, czy kolumna to klucz obcy (np. id_pracownika w Instruktor)
            if column.startswith("id_") and column != f"id_{table_name.lower()}":
                referenced_table = self.get_referenced_table(column)
                if referenced_table:
                    ttk.Label(form, text=column).grid(row=i, column=0)
                    options = self.get_readable_options(referenced_table)
                    combobox = ttk.Combobox(form, values=options, state="readonly")
                    combobox.grid(row=i, column=1)
                    if data:
                        readable_value = self.get_readable_value(referenced_table, data[i])
                        combobox.set(readable_value)
                    entries[column] = combobox
                    continue

            ttk.Label(form, text=column).grid(row=i, column=0)
            entry = ttk.Entry(form)
            entry.grid(row=i, column=1)
            if data:
                entry.insert(0, data[i])
            entries[column] = entry

        def save():
            values = {}
            for col, widget in entries.items():
                if isinstance(widget, ttk.Combobox):
                    values[col] = self.get_id_from_readable(referenced_table, widget.get())
                else:
                    values[col] = widget.get()

            try:
                if data:
                    # Update
                    set_clause = ", ".join([f"{col} = %s" for col in values.keys()])
                    query = f"UPDATE {table_name} SET {set_clause} WHERE {list(values.keys())[0]} = %s;"
                    self.cursor.execute(query, tuple(values.values()) + (data[0],))
                else:
                    # Insert
                    cols = ", ".join(values.keys())
                    placeholders = ", ".join(["%s"] * len(values))
                    query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders});"
                    self.cursor.execute(query, tuple(values.values()))

                self.conn.commit()
                self.update_table_view()
                messagebox.showinfo("Sukces", "Rekord został zapisany")
                form.destroy()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zapisać rekordu: {e}")

        ttk.Button(form, text="Zapisz", command=save).grid(row=len(columns), column=0, columnspan=2)

    def get_referenced_table(self, column):
        # Mapowanie kolumn kluczy obcych na tabele referencyjne
        mapping = {
            "id_klienta": "Klienci",
            "id_pracownika": "Pracownicy",
            "id_czlonkostwa": "Czlonkostwo",
            "id_zajec": "Zajecia",
            "id_sprzetu": "Sprzet",
            "id_rezerwacji": "Rezerwacja_sprzetu",
            "id_platnosci": "Platnosc",
            "id_wydarzenia": "Wydarzenia",
            "id_anulowania": "Anulowanie",
            "id_placowki": "Placowki",
            "id_oceny": "Ocena_instruktorow",
            "id_grafiku": "Grafik_pracownikow",
            "id_instruktora": "Instruktor",
            "None":"None"
        }
        return mapping.get(column)

    def get_readable_options(self, table_name):
        try:
            if table_name == "Klienci":
                self.cursor.execute("SELECT id_klienta, imie, nazwisko FROM Klienci")
                return [f"{row[1]} {row[2]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Pracownicy":
                self.cursor.execute("SELECT id_pracownika, imie, nazwisko FROM Pracownicy")
                return [f"{row[1]} {row[2]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Instruktor":
                self.cursor.execute("SELECT Pracownicy.id_pracownika, Pracownicy.imie, Pracownicy.nazwisko FROM Instruktor, Pracownicy WHERE Instruktor.id_pracownika = Pracownicy.id_pracownika")
                return [f"{row[1]} {row[2]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Zajecia":
                self.cursor.execute("SELECT id_zajec, nazwa_zajec, data_i_godzina FROM Zajecia")
                return [f"{row[1]} {row[2]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Sprzet":
                self.cursor.execute("SELECT id_sprzetu, nazwa FROM Sprzet")
                return [f"{row[1]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Rezerwacja_sprzetu":
                self.cursor.execute("SELECT id_rezerwacji, id_sprzetu, id_klienta FROM Rezerwacja_sprzetu")
                return [f"ID: {row[0]} (Sprzęt: {row[1]}, Klient: {row[2]})" for row in self.cursor.fetchall()]
            elif table_name == "Platnosc":
                self.cursor.execute("SELECT id_platnosci, kwota, data_platnosci FROM Platnosc")
                return [f"{row[1]} PLN ({row[2]}) (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Wydarzenia":
                self.cursor.execute("SELECT id_wydarzenia, nazwa, data FROM Wydarzenia")
                return [f"{row[1]} {row[2]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Anulowanie_czlonkostwa":
                self.cursor.execute("SELECT id_anulowania, powod_zamkniecia, id_czlonkostwa FROM Anulowanie_czlonkostwa")
                return [f"ID: {row[0]} {row[2]} (Członkostwo: {row[1]})" for row in self.cursor.fetchall()]
            elif table_name == "Placowki":
                self.cursor.execute("SELECT id_placowki, nazwa FROM Placowki")
                return [f"{row[1]} (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Ocena_instruktorow":
                self.cursor.execute("SELECT id_oceny, ocena, id_klienta FROM Ocena_instruktorow")
                return [f"Ocena: {row[1]} (Instruktor: {row[2]}) (ID: {row[0]})" for row in self.cursor.fetchall()]
            elif table_name == "Grafik_pracownikow":
                self.cursor.execute("SELECT id_grafiku, id_pracownika, data, godzina_rozpoczecia, godzina_zakonczenia FROM Grafik_pracownikow")
                return [f"ID: {row[0]} {row[2]} {row[3]} : {row[4]} (Pracownik: {row[1]})" for row in self.cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się pobrać danych: {e}")
            return []

    def get_id_from_readable(self, table_name, readable):
        match = re.search(r"\(ID: (\d+)\)", readable)
        return int(match.group(1)) if match else None

    def get_readable_value(self, table_name, id_value):
        try:
            if table_name == "Klienci" and id_value != "None":
                self.cursor.execute("SELECT imie, nazwisko FROM Klienci WHERE id_klienta = %s", (id_value,))
            elif table_name == "Pracownicy" and id_value != "None":
                self.cursor.execute("SELECT imie, nazwisko FROM Pracownicy WHERE id_pracownika = %s", (id_value,))
            elif table_name == "Instruktor" and id_value != "None":
                self.cursor.execute("SELECT id_pracownika FROM Instruktor WHERE id_pracownika = %s", (id_value,))
            elif table_name == "Zajecia" and id_value != "None":
                self.cursor.execute("SELECT nazwa_zajec, data_i_godzina FROM Zajecia WHERE id_zajec = %s", (id_value,))
            elif table_name == "Sprzet" and id_value != "None":
                self.cursor.execute("SELECT nazwa FROM Sprzet WHERE id_sprzetu = %s", (id_value,))
            elif table_name == "Rezerwacja_sprzetu" and id_value != "None":
                self.cursor.execute("SELECT id_sprzetu, id_klienta FROM Rezerwacja_sprzetu WHERE id_rezerwacji = %s", (id_value,))
            elif table_name == "Platnosc" and id_value != "None":
                self.cursor.execute("SELECT kwota, data_platnosci FROM Platnosc WHERE id_platnosci = %s", (id_value,))
            elif table_name == "Wydarzenia" and id_value != "None":
                self.cursor.execute("SELECT nazwa, data FROM Wydarzenia WHERE id_wydarzenia = %s", (id_value,))
            elif table_name == "Anulowanie_czlonkostwa":
                self.cursor.execute("SELECT powod_zamkniecia, id_czlonkostwa FROM Anulowanie_czlonkostwa WHERE id_anulowania = %s", (id_value,))
            elif table_name == "Placowki" and id_value != "None":
                self.cursor.execute("SELECT nazwa FROM Placowki WHERE id_placowki = %s", (id_value,))
            elif table_name == "Ocena_instruktorow" and id_value != "None":
                self.cursor.execute("SELECT ocena, id_klienta FROM Ocena_instruktorow WHERE id_oceny = %s", (id_value,))
            elif table_name == "Grafik_pracownikow" and id_value != "None":
                self.cursor.execute("SELECT id_pracownika, data, godzina_rozpoczecia, godzina_zakonczenia FROM Grafik_pracownikow WHERE id_grafiku = %s", (id_value,))
            elif id_value == "None":
                return ""
            row = self.cursor.fetchone()
            return f"{row[0]} {row[1]}" if row else "Test"
        except Exception as e:
            return None

    def run(self):
        self.connect_to_db()
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = GymApp(root)
    app.run()