import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from .env")

try:
    with psycopg.connect(
        database_url,
        connect_timeout=10
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    current_database(),
                    current_user,
                    version()
            """)

            result = cur.fetchone()

    print("SUPABASE CONNECTION SUCCESSFUL")
    print("Database:", result[0])
    print("User:", result[1])
    print("PostgreSQL version:", result[2].split(",")[0])

except Exception as error:
    print("SUPABASE CONNECTION FAILED")
    print("Error:", str(error))