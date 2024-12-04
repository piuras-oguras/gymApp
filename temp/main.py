import flet as ft
from db import execute_query


def main(page: ft.Page):
    table_container = ft.Container(padding=10, expand=True)
    appbar_text_ref = ft.Ref[ft.Text]()
    tables = {
        "klienci": ["imie", "nazwisko", "data_urodzenia", "data_rejestracji", "numer_telefonu", "email"],
        "Pracownicy": ["imie", "nazwisko", "adres", "data_urodzenia", "data_zatrudnienia", "stawka_godzinowa", "email", "numer_telefonu", "status"],
        "zajecia": ["nazwa_zajęc", "data_i_godzina", "maksymalna_ilosc_uczestnikow", "lokalizacja_w sioowni"],
    }
    def show_table(table_name):
        data = execute_query(f"SELECT * FROM klienci")
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
    page.appbar = ft.AppBar(
        title=ft.Text("GymApp", ref=appbar_text_ref),
        center_title=True,
        bgcolor=ft.Colors.BLUE,
    )

    menubar = ft.MenuBar(
        expand=True,
        style=ft.MenuStyle(
            alignment=ft.alignment.top_left,
            bgcolor=ft.Colors.RED_300,
            mouse_cursor={
                ft.ControlState.HOVERED: ft.MouseCursor.WAIT,
                ft.ControlState.DEFAULT: ft.MouseCursor.ZOOM_OUT,
            },
        ),
        controls=[
            ft.SubmenuButton(
                content=ft.Text("Tabele"),
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Klienci"),
                        leading=ft.Icon(ft.Icons.INFO),
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.HOVERED: ft.Colors.GREEN_100}
                        ),
                        on_click=show_table,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Save"),
                        leading=ft.Icon(ft.Icons.SAVE),
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.HOVERED: ft.Colors.GREEN_100}
                        ),
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Quit"),
                        leading=ft.Icon(ft.Icons.CLOSE),
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.HOVERED: ft.Colors.GREEN_100}
                        ),
                    ),
                ],
            ),
            ft.SubmenuButton(
                content=ft.Text("Tabela"),
                controls=[
                    ft.SubmenuButton(
                        content=ft.Text("Zoom"),
                        controls=[
                            ft.MenuItemButton(
                                content=ft.Text("Magnify"),
                                leading=ft.Icon(ft.Icons.ZOOM_IN),
                                close_on_click=False,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.HOVERED: ft.Colors.PURPLE_200
                                    }
                                ),
                            ),
                            ft.MenuItemButton(
                                content=ft.Text("Minify"),
                                leading=ft.Icon(ft.Icons.ZOOM_OUT),
                                close_on_click=False,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.HOVERED: ft.Colors.PURPLE_200
                                    }
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ],
    )

    page.add(ft.Row([menubar, table_container]))


ft.app(main)