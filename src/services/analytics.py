
from src.database.db import get_connection


def get_dashboard_metrics():
    conn = get_connection()
    try:
        def value(sql):
            return list(conn.execute(sql).fetchone().values())[0]

        total_equipment = value(
            "SELECT COUNT(*) AS v FROM equipment"
        )

        rented_equipment = value(
            "SELECT COUNT(*) AS v FROM equipment WHERE status = 'rented'"
        )

        total_rental_value = value(
            "SELECT COALESCE(SUM(rental_amount), 0) AS v FROM rentals"
        )

        total_collected = value(
            "SELECT COALESCE(SUM(amount), 0) AS v FROM payments"
        )

        outstanding = value("""
            SELECT COALESCE(SUM(i.amount - COALESCE(p.paid, 0)), 0) AS v
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
        """)

        active_rentals = value(
            "SELECT COUNT(*) AS v FROM rentals WHERE status = 'active'"
        )

        pending_quotations = value(
            "SELECT COUNT(*) AS v FROM quotations WHERE status = 'pending'"
        )

        overdue_invoices = value("""
            SELECT COUNT(*) AS v
            FROM invoices i
            WHERE i.due_date < CURRENT_DATE
            AND i.amount > COALESCE((
                SELECT SUM(p.amount)
                FROM payments p
                WHERE p.invoice_id = i.id
            ), 0)
        """)

        utilization = (
            round(rented_equipment / total_equipment * 100, 1)
            if total_equipment else 0
        )

        return {
            "total_equipment": total_equipment,
            "rented_equipment": rented_equipment,
            "utilization": utilization,
            "total_rental_value": round(float(total_rental_value), 2),
            "total_collected": round(float(total_collected), 2),
            "outstanding": round(float(outstanding), 2),
            "active_rentals": active_rentals,
            "pending_quotations": pending_quotations,
            "overdue_invoices": overdue_invoices
        }
    finally:
        conn.close()


def get_monthly_rental_data():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                TO_CHAR(start_date, 'YYYY-MM') AS month,
                SUM(rental_amount) AS amount
            FROM rentals
            GROUP BY TO_CHAR(start_date, 'YYYY-MM')
            ORDER BY month
        """).fetchall()

        return [
            {"month": row["month"], "amount": float(row["amount"] or 0)}
            for row in rows
        ]
    finally:
        conn.close()


def get_equipment_data():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT category, COUNT(*) AS total
            FROM equipment
            GROUP BY category
            ORDER BY total DESC
        """).fetchall()

        return [
            {"category": row["category"], "total": row["total"]}
            for row in rows
        ]
    finally:
        conn.close()


def get_top_equipment():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT e.name, SUM(r.rental_amount) AS rental_value
            FROM rentals r
            JOIN equipment e ON e.id = r.equipment_id
            GROUP BY e.id, e.name
            ORDER BY rental_value DESC
            LIMIT 5
        """).fetchall()

        return [
            {"name": row["name"], "value": float(row["rental_value"] or 0)}
            for row in rows
        ]
    finally:
        conn.close()
