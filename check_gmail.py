from src.database.db import get_connection

conn = get_connection()

rows = conn.execute("""
    SELECT source_id, sender, subject, content, timestamp, category
    FROM communications
    WHERE source = 'gmail'
    ORDER BY timestamp DESC
""").fetchall()

print(f"\nTotal Gmail records: {len(rows)}\n")

for row in rows:
    print("-" * 60)
    print("ID:", row["source_id"])
    print("FROM:", row["sender"])
    print("SUBJECT:", row["subject"])
    print("CATEGORY:", row["category"])
    print("CONTENT:", row["content"][:300])
    print("DATE:", row["timestamp"])

conn.close()