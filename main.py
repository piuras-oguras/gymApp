import flet as ft
from db import execute_query

def main(page: ft.Page):
    page.title = "Zarządzanie siłownią"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.START

    # Kontenery interfejsu
    menu = ft.Column(width=200, spacing=10)
    table_container = ft.Container(padding=10, expand=True)
    form_container = ft.Container(padding=10, expand=True)

    # Funkcja do załadowania danych z tabeli
    def show_table(table_name):
        data = execute_query(f"SELECT * FROM {table_name}")
        columns = data[0].keys() if data else []
        rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(str(row[col]))) for col in columns])
            for row in data
        ]
        table_container.content = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in columns],
            rows=rows
        )
        page.update()

    # Funkcja do tworzenia formularza dodawania danych
    def create_form(table_name, fields):
        inputs = {field: ft.TextField(label=field) for field in fields}
        form_container.content = ft.Column(
            list(inputs.values()) + [
                ft.ElevatedButton(
                    "Dodaj rekord",
                    on_click=lambda _: add_record(table_name, {k: v.value for k, v in inputs.items()})
                )
            ]
        )
        page.update()

    # Funkcja dodająca rekord do tabeli
    def add_record(table_name, data):
        keys = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({values})"
        execute_query(query, list(data.values()))
        ft.toast(f"Rekord dodany do tabeli {table_name}!")
        show_table(table_name)

    # Funkcja usuwająca rekord
    def delete_record(table_name, record_id):
        query = f"DELETE FROM {table_name} WHERE id = %s"
        execute_query(query, [record_id])
        ft.toast(f"Rekord o ID {record_id} usunięty!")
        show_table(table_name)

    # Menu wyboru tabel
    tables = {
        "Klienci": ["imie", "nazwisko", "data_urodzenia", "data_rejestracji", "numer_telefonu", "email"],
        "Pracownicy": ["imie", "nazwisko", "adres", "data_urodzenia", "data_zatrudnienia", "stawka_godzinowa", "email", "numer_telefonu", "status"],
        "Zajęcia": ["nazwa_zajęc", "data_i_godzina", "maksymalna_ilosc_uczestnikow", "lokalizacja_w sioowni"],
    }

    for table_name, fields in tables.items():
        menu.controls.append(
            ft.TextButton(
                table_name,
                on_click=lambda e, t=table_name: (
                    show_table(t),
                    create_form(t, tables[t])
                )
            )
        )

    # Layout strony
    page.add(ft.Row([menu, table_container, form_container], expand=True))

ft.app(target=main)
