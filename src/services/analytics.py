from src.database.db import get_connection


def get_dashboard_metrics():
    conn = get_connection()

    total_equipment = conn.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]

    rented_equipment = conn.execute(
        "SELECT COUNT(*) FROM equipment WHERE status = 'rented'"
    ).fetchone()[0]

    total_rental_value = conn.execute(
        "SELECT COALESCE(SUM(rental_amount), 0) FROM rentals"
    ).fetchone()[0]

    total_collected = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM payments"
    ).fetchone()[0]

    outstanding = conn.execute("""
        SELECT COALESCE(SUM(
            i.amount - COALESCE(p.paid, 0)
        ), 0)
        FROM invoices i
        LEFT JOIN (
            SELECT invoice_id, SUM(amount) AS paid
            FROM payments
            GROUP BY invoice_id
        ) p ON i.id = p.invoice_id
    """).fetchone()[0]

    active_rentals = conn.execute(
        "SELECT COUNT(*) FROM rentals WHERE status = 'active'"
    ).fetchone()[0]

    pending_quotations = conn.execute(
        "SELECT COUNT(*) FROM quotations WHERE status = 'pending'"
    ).fetchone()[0]

    overdue_invoices = conn.execute("""
        SELECT COUNT(*)
        FROM invoices i
        WHERE i.due_date < date('now')
        AND i.amount > COALESCE((
            SELECT SUM(p.amount)
            FROM payments p
            WHERE p.invoice_id = i.id
        ), 0)
    """).fetchone()[0]

    utilization = (
        round(rented_equipment / total_equipment * 100, 1)
        if total_equipment else 0
    )

    conn.close()

    return {
        "total_equipment": total_equipment,
        "rented_equipment": rented_equipment,
        "utilization": utilization,
        "total_rental_value": round(total_rental_value, 2),
        "total_collected": round(total_collected, 2),
        "outstanding": round(outstanding, 2),
        "active_rentals": active_rentals,
        "pending_quotations": pending_quotations,
        "overdue_invoices": overdue_invoices
    }


def get_monthly_rental_data():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            strftime('%Y-%m', start_date) AS month,
            SUM(rental_amount) AS amount
        FROM rentals
        GROUP BY month
        ORDER BY month
    """).fetchall()

    conn.close()

    return [
        {"month": row["month"], "amount": row["amount"]}
        for row in rows
    ]


def get_equipment_data():
    conn = get_connection()

    rows = conn.execute("""
        SELECT category, COUNT(*) AS total
        FROM equipment
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()

    conn.close()

    return [
        {"category": row["category"], "total": row["total"]}
        for row in rows
    ]


def get_top_equipment():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            e.name,
            SUM(r.rental_amount) AS rental_value
        FROM rentals r
        JOIN equipment e ON e.id = r.equipment_id
        GROUP BY e.id, e.name
        ORDER BY rental_value DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return [
        {"name": row["name"], "value": row["rental_value"]}
        for row in rows
    ]
