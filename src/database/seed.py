import random
from datetime import date, timedelta
from src.database.db import get_connection

random.seed(42)

def seed_database():
    conn = get_connection()
    cur = conn.cursor()

    # Reset only our synthetic demo records.
    for table in [
        "payments", "invoices", "maintenance", "rentals",
        "quotations", "communications", "equipment", "customers"
    ]:
        cur.execute(f"DELETE FROM {table}")

    customers = [
        ("Rajesh Patil", "Patil Infra Projects", "9876501001", "rajesh@patilinfra.example", "Pune"),
        ("Amit Sharma", "Sharma Construction", "9876501002", "amit@sharmaconstruction.example", "Mumbai"),
        ("Neha Deshmukh", "ND Developers", "9876501003", "neha@nddevelopers.example", "Nashik"),
        ("Vikram Rao", "Rao Infrastructure", "9876501004", "vikram@raoinfra.example", "Nagpur"),
        ("Sanjay Mehta", "Mehta Roads", "9876501005", "sanjay@mehtaroads.example", "Aurangabad"),
        ("Priya Kulkarni", "PK Engineering", "9876501006", "priya@pkengineering.example", "Pune"),
        ("Rohit Verma", "Verma Builders", "9876501007", "rohit@vermabuilders.example", "Kolhapur"),
        ("Anil Joshi", "AJ Mining", "9876501008", "anil@ajmining.example", "Chandrapur"),
        ("Karan Shah", "Shah Developers", "9876501009", "karan@shahdev.example", "Mumbai"),
        ("Meera Nair", "Nair Projects", "9876501010", "meera@nairprojects.example", "Nashik"),
    ]

    cur.executemany("""
        INSERT INTO customers (name, company, phone, email, location)
        VALUES (?, ?, ?, ?, ?)
    """, customers)

    equipment = [
        ("CAT 320D Excavator", "Excavator", "CAT 320D", "MH01-EX-1001", 18000, "rented"),
        ("JCB 3DX Backhoe", "Backhoe Loader", "JCB 3DX", "MH01-BH-1002", 9000, "available"),
        ("Tata Hitachi EX200", "Excavator", "EX200", "MH01-EX-1003", 16000, "rented"),
        ("Komatsu D85 Bulldozer", "Bulldozer", "D85", "MH01-BD-1004", 22000, "available"),
        ("ACE 14XW Crane", "Crane", "14XW", "MH01-CR-1005", 25000, "rented"),
        ("Volvo L120 Loader", "Wheel Loader", "L120", "MH01-WL-1006", 14000, "available"),
        ("CAT 424 Backhoe", "Backhoe Loader", "CAT 424", "MH01-BH-1007", 10000, "maintenance"),
        ("SANY SY215 Excavator", "Excavator", "SY215", "MH01-EX-1008", 17000, "rented"),
        ("Tata Prima Dumper", "Dumper", "Prima", "MH01-DP-1009", 12000, "available"),
        ("JCB 220 Excavator", "Excavator", "JCB 220", "MH01-EX-1010", 19000, "rented"),
        ("ACE Hydra Crane", "Crane", "Hydra 14T", "MH01-CR-1011", 15000, "available"),
        ("CAT 950 Loader", "Wheel Loader", "CAT 950", "MH01-WL-1012", 16000, "maintenance"),
    ]

    cur.executemany("""
        INSERT INTO equipment
        (name, category, model, registration_number, daily_rate, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, equipment)

    today = date(2026, 10, 31)

    # customer_id, equipment_id, start date, duration, daily rate, status
    rental_specs = [
        (1, 1, "2026-07-05", 30, 18000, "completed"),
        (2, 3, "2026-07-15", 25, 16000, "completed"),
        (3, 5, "2026-08-01", 20, 25000, "completed"),
        (4, 8, "2026-08-10", 30, 17000, "completed"),
        (5, 10, "2026-08-20", 15, 19000, "completed"),
        (6, 2, "2026-09-01", 20, 9000, "completed"),
        (7, 4, "2026-09-05", 15, 22000, "completed"),
        (8, 9, "2026-09-10", 25, 12000, "completed"),
        (9, 1, "2026-09-20", 30, 18000, "completed"),
        (10, 6, "2026-09-25", 20, 14000, "completed"),
        (1, 3, "2026-10-01", 45, 16000, "active"),
        (2, 5, "2026-10-05", 30, 25000, "active"),
        (3, 8, "2026-10-08", 30, 17000, "active"),
        (4, 10, "2026-10-10", 25, 19000, "active"),
        (5, 1, "2026-10-12", 20, 18000, "active"),
        (6, 2, "2026-10-15", 10, 9000, "active"),
        (7, 9, "2026-10-18", 15, 12000, "active"),
        (8, 11, "2026-10-20", 12, 15000, "active"),
    ]

    rental_ids = []

    for customer_id, equipment_id, start, days, rate, status in rental_specs:
        start_date = date.fromisoformat(start)
        end_date = start_date + timedelta(days=days)
        amount = days * rate

        cur.execute("""
            INSERT INTO rentals
            (customer_id, equipment_id, start_date, end_date, rental_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, equipment_id, start, end_date.isoformat(), amount, status))

        rental_ids.append((cur.lastrowid, customer_id, amount, start_date))

    # Create invoices and payments for each rental.
    for index, (rental_id, customer_id, amount, start_date) in enumerate(rental_ids, 1):
        due_date = start_date + timedelta(days=30)

        if index % 4 == 0:
            status = "unpaid"
            paid = 0
        elif index % 4 == 1:
            status = "paid"
            paid = amount
        elif index % 4 == 2:
            status = "partial"
            paid = round(amount * 0.5, 2)
        else:
            status = "paid"
            paid = amount

        cur.execute("""
            INSERT INTO invoices
            (customer_id, rental_id, invoice_number, amount, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, rental_id, f"INV-2026-{index:04d}",
              amount, due_date.isoformat(), status))

        invoice_id = cur.lastrowid

        if paid > 0:
            cur.execute("""
                INSERT INTO payments (invoice_id, amount, payment_date, method)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, paid, today.isoformat(), "Bank Transfer"))

    quotations = [
        (1, 4, 330000, "pending", "2026-10-20"),
        (2, 1, 540000, "approved", "2026-10-21"),
        (3, 5, 500000, "pending", "2026-10-22"),
        (4, 8, 510000, "rejected", "2026-10-23"),
        (5, 10, 380000, "pending", "2026-10-24"),
        (6, 3, 240000, "approved", "2026-10-25"),
        (7, 6, 280000, "pending", "2026-10-26"),
        (8, 9, 180000, "pending", "2026-10-27"),
    ]

    cur.executemany("""
        INSERT INTO quotations
        (customer_id, equipment_id, amount, status, quotation_date)
        VALUES (?, ?, ?, ?, ?)
    """, quotations)

    maintenance = [
        (7, "Hydraulic system inspection", "2026-10-28", 18000, "in progress"),
        (12, "Engine servicing", "2026-10-25", 25000, "pending"),
        (2, "Routine inspection", "2026-09-15", 8000, "completed"),
        (4, "Undercarriage repair", "2026-08-20", 32000, "completed"),
    ]

    cur.executemany("""
        INSERT INTO maintenance
        (equipment_id, description, maintenance_date, cost, status)
        VALUES (?, ?, ?, ?, ?)
    """, maintenance)

    communications = [
        ("gmail", "MAIL-001", None, "Rajesh Patil", "Excavator quotation",
         "Requesting a quotation for a CAT excavator for a construction project.",
         "2026-10-20", "sales"),
        ("gmail", "MAIL-002", None, "Accounts Team", "Pending invoice",
         "Invoice INV-2026-0004 is awaiting payment confirmation.",
         "2026-10-25", "accounts"),
        ("whatsapp", "WA-001", "rental-sales-group", "Site Manager", None,
         "The excavator deployment is confirmed for the Pune project.",
         "2026-10-27", "operations"),
        ("whatsapp", "WA-002", "rental-sales-group", "Sales Manager", None,
         "Follow up with the customer regarding the pending crane quotation.",
         "2026-10-28", "sales"),
        ("drive", "DOC-001", None, "Accounts", "October rental summary",
         "Synthetic October rental and invoice summary for demonstration.",
         "2026-10-30", "accounts"),
    ]

    cur.executemany("""
        INSERT INTO communications
        (source, source_id, group_id, sender, subject, content, timestamp, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, communications)

    conn.commit()
    conn.close()

    print("Synthetic rental dataset created successfully.")
    print("Customers: 10 | Equipment: 12 | Rentals: 18")
    print("Invoices: 18 | Quotations: 8 | Maintenance: 4")
    print("Communications: 5")


if __name__ == "__main__":
    seed_database()
