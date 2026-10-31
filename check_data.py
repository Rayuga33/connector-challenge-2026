from src.database.db import get_connection

conn = get_connection()

tables = [
    "customers",
    "equipment",
    "rentals",
    "quotations",
    "invoices",
    "payments",
    "maintenance",
    "communications"
]

for table in tables:
    count = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count} records")

conn.close()