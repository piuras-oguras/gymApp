import psycopg2
from psycopg2.extras import RealDictCursor

# Funkcja do nawiązania połączenia z bazą danych
def get_connection():
    conn =psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="szymon",
        host="localhost",
        port=5432
    )
    return conn

# Funkcja wykonująca zapytania SQL
def execute_query(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if query.strip().lower().startswith("select"):
                return cur.fetchall()
            conn.commit()