import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "instance" / "equipintel.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def initialize_database():
    conn = get_connection()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company TEXT,
        phone TEXT,
        email TEXT,
        location TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        model TEXT,
        registration_number TEXT UNIQUE,
        daily_rate REAL DEFAULT 0,
        status TEXT DEFAULT 'available',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS quotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        equipment_id INTEGER,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        quotation_date TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(equipment_id) REFERENCES equipment(id)
    );

    CREATE TABLE IF NOT EXISTS rentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        equipment_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        rental_amount REAL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(equipment_id) REFERENCES equipment(id)
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        rental_id INTEGER,
        invoice_number TEXT UNIQUE,
        amount REAL NOT NULL,
        due_date TEXT,
        status TEXT DEFAULT 'unpaid',
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(rental_id) REFERENCES rentals(id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        amount REAL NOT NULL,
        payment_date TEXT,
        method TEXT,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    );

    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER,
        description TEXT,
        maintenance_date TEXT,
        cost REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(equipment_id) REFERENCES equipment(id)
    );

    CREATE TABLE IF NOT EXISTS communications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        group_id TEXT,
        sender TEXT,
        subject TEXT,
        content TEXT NOT NULL,
        timestamp TEXT,
        category TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source, source_id)
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print(f"EquipIntel database initialized: {DB_PATH}")
