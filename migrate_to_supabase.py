
import os
from dotenv import load_dotenv
import psycopg
from src.database.db import get_local_connection as get_connection

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ORG_ID = "a94a6421-0db0-40f2-850a-7e6ba623eff0"

TABLES = {
    "customers": [
        "id", "name", "company", "phone", "email", "location"
    ],
    "equipment": [
        "id", "name", "category", "model", "registration_number",
        "daily_rate", "status"
    ],
    "rentals": [
        "id", "customer_id", "equipment_id", "start_date",
        "end_date", "rental_amount", "status"
    ],
    "invoices": [
        "id", "customer_id", "rental_id", "invoice_number",
        "amount", "due_date", "status"
    ],
    "payments": [
        "id", "invoice_id", "amount", "payment_date", "method"
    ],
    "quotations": [
        "id", "customer_id", "equipment_id", "amount",
        "status", "quotation_date"
    ],
    "maintenance": [
        "id", "equipment_id", "description", "maintenance_date",
        "cost", "status"
    ],
    "communications": [
        "id", "source", "source_id", "group_id", "sender",
        "subject", "content", "timestamp", "category"
    ]
}

def migrate():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL missing from .env")

    sqlite_conn = get_connection()

    try:
        with psycopg.connect(DATABASE_URL) as pg_conn:
            with pg_conn.cursor() as cur:

                # Confirm organization exists.
                cur.execute(
                    "SELECT id FROM organizations WHERE id = %s",
                    (ORG_ID,)
                )
                if not cur.fetchone():
                    raise RuntimeError("Demo organization not found.")

                for table, columns in TABLES.items():
                    rows = sqlite_conn.execute(
                        f"SELECT {', '.join(columns)} FROM {table}"
                    ).fetchall()

                    if not rows:
                        print(f"{table}: no local records")
                        continue

                    column_sql = ", ".join(
                        ["organization_id"] + columns
                    )
                    placeholders = ", ".join(
                        ["%s"] * (len(columns) + 1)
                    )

                    sql = f"""
                        INSERT INTO {table} ({column_sql})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                    """

                    values = [
                        (ORG_ID,) + tuple(row[column] for column in columns)
                        for row in rows
                    ]

                    cur.executemany(sql, values)
                    print(f"{table}: processed {len(rows)} local records")

            pg_conn.commit()

        print("\nMIGRATION COMPLETED")

    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    migrate()
