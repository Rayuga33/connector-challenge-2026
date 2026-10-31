from src.database.db import get_connection


def answer_question(question):
    q = question.lower().strip()
    conn = get_connection()

    try:
        # 1. Outstanding customer payments
        if any(word in q for word in ["outstanding", "unpaid", "pending payment", "dues"]):
            rows = conn.execute("""
                SELECT
                    c.name AS customer,
                    i.invoice_number,
                    i.amount,
                    i.due_date,
                    i.status,
                    COALESCE(SUM(p.amount), 0) AS paid,
                    i.amount - COALESCE(SUM(p.amount), 0) AS balance
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id
                HAVING balance > 0
                ORDER BY balance DESC
            """).fetchall()

            total = sum(row["balance"] for row in rows)
            details = [
                f'{r["customer"]}: invoice {r["invoice_number"]}, '
                f'balance ₹{r["balance"]:,.0f}, due {r["due_date"]}'
                for r in rows
            ]

            return {
                "answer": (
                    f"There are {len(rows)} invoices with outstanding balances "
                    f"totalling ₹{total:,.0f}.\n" + "\n".join(details[:10])
                ),
                "sources": [
                    {
                        "table": "invoices",
                        "record_id": r["invoice_number"],
                        "detail": f'{r["customer"]} — outstanding ₹{r["balance"]:,.0f}'
                    }
                    for r in rows
                ]
            }

        # 2. Top-performing equipment
        if any(word in q for word in ["top equipment", "best equipment", "most revenue",
                                       "highest rental", "equipment generates"]):
            rows = conn.execute("""
                SELECT e.name, SUM(r.rental_amount) AS rental_value
                FROM rentals r
                JOIN equipment e ON e.id = r.equipment_id
                GROUP BY e.id, e.name
                ORDER BY rental_value DESC
                LIMIT 5
            """).fetchall()

            answer = "Top equipment by recorded rental contract value:\n"
            answer += "\n".join(
                f'{i}. {r["name"]}: ₹{r["rental_value"]:,.0f}'
                for i, r in enumerate(rows, 1)
            )

            return {
                "answer": answer,
                "sources": [
                    {
                        "table": "equipment and rentals",
                        "record_id": r["name"],
                        "detail": f'Recorded rental value ₹{r["rental_value"]:,.0f}'
                    }
                    for r in rows
                ]
            }

        # 3. Active rentals
        if "active rental" in q or "ongoing rental" in q:
            rows = conn.execute("""
                SELECT r.id, c.name AS customer, e.name AS equipment,
                       r.start_date, r.end_date, r.rental_amount
                FROM rentals r
                JOIN customers c ON c.id = r.customer_id
                JOIN equipment e ON e.id = r.equipment_id
                WHERE r.status = 'active'
                ORDER BY r.start_date
            """).fetchall()

            answer = f"There are {len(rows)} active rental contracts.\n"
            answer += "\n".join(
                f'{r["customer"]} — {r["equipment"]}, '
                f'{r["start_date"]} to {r["end_date"]}'
                for r in rows
            )

            return {
                "answer": answer,
                "sources": [
                    {
                        "table": "rentals",
                        "record_id": r["id"],
                        "detail": f'{r["customer"]} — {r["equipment"]}'
                    }
                    for r in rows
                ]
            }

        # 4. Overdue invoices
        if "overdue" in q or "past due" in q:
            rows = conn.execute("""
                SELECT i.invoice_number, i.amount, i.due_date,
                       c.name AS customer,
                       i.amount - COALESCE(
                           (SELECT SUM(p.amount) FROM payments p
                            WHERE p.invoice_id = i.id), 0
                       ) AS balance
                FROM invoices i
                JOIN customers c ON c.id = i.customer_id
                WHERE i.due_date < date('now')
                AND i.amount > COALESCE(
                    (SELECT SUM(p.amount) FROM payments p
                     WHERE p.invoice_id = i.id), 0
                )
                ORDER BY i.due_date
            """).fetchall()

            answer = f"There are {len(rows)} overdue unpaid invoices.\n"
            answer += "\n".join(
                f'{r["customer"]} — {r["invoice_number"]}: '
                f'₹{r["balance"]:,.0f}, due {r["due_date"]}'
                for r in rows
            )

            return {
                "answer": answer,
                "sources": [
                    {
                        "table": "invoices",
                        "record_id": r["invoice_number"],
                        "detail": f'{r["customer"]} — overdue balance ₹{r["balance"]:,.0f}'
                    }
                    for r in rows
                ]
            }

        # 5. Pending quotations
        if "quotation" in q:
            rows = conn.execute("""
                SELECT q.id, c.name AS customer, e.name AS equipment,
                       q.amount, q.quotation_date
                FROM quotations q
                JOIN customers c ON c.id = q.customer_id
                JOIN equipment e ON e.id = q.equipment_id
                WHERE q.status = 'pending'
                ORDER BY q.quotation_date DESC
            """).fetchall()

            answer = f"There are {len(rows)} pending quotations.\n"
            answer += "\n".join(
                f'{r["customer"]} — {r["equipment"]}: '
                f'₹{r["amount"]:,.0f}'
                for r in rows
            )

            return {
                "answer": answer,
                "sources": [
                    {
                        "table": "quotations",
                        "record_id": r["id"],
                        "detail": f'{r["customer"]} — {r["equipment"]}, ₹{r["amount"]:,.0f}'
                    }
                    for r in rows
                ]
            }

        # 6. Equipment inventory
        if any(word in q for word in ["how many equipment", "total equipment",
                                       "fleet size", "equipment count"]):
            rows = conn.execute("""
                SELECT category, COUNT(*) AS total
                FROM equipment
                GROUP BY category
                ORDER BY total DESC
            """).fetchall()

            total = sum(r["total"] for r in rows)
            answer = f"The fleet contains {total} equipment assets.\n"
            answer += "\n".join(
                f'{r["category"]}: {r["total"]}'
                for r in rows
            )

            return {
                "answer": answer,
                "sources": [
                    {
                        "table": "equipment",
                        "record_id": r["category"],
                        "detail": f'{r["total"]} assets'
                    }
                    for r in rows
                ]
            }

        # 7. Total payments collected
        if "payment" in q or "collected" in q:
            row = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM payments
            """).fetchone()

            return {
                "answer": f"Total recorded payments collected: ₹{row['total']:,.0f}.",
                "sources": [
                    {
                        "table": "payments",
                        "record_id": "all payment records",
                        "detail": "Sum of recorded payment amounts"
                    }
                ]
            }

        return {
            "answer": (
                "I couldn't confidently answer that from the available data. "
                "Try asking about outstanding payments, overdue invoices, "
                "active rentals, equipment performance, quotations, or payments collected."
            ),
            "sources": []
        }

    finally:
        conn.close()
