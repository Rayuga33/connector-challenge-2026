
import os
import base64
from datetime import datetime, timezone
from email.utils import parseaddr

from dotenv import load_dotenv
from src.connectors.gmail_service import get_gmail_service
from src.database.db import get_connection

load_dotenv()

ORG_ID = "a94a6421-0db0-40f2-850a-7e6ba623eff0"

DEFAULT_QUERY = "newer_than:90d"
MAX_MESSAGES = 100


def decode_body(payload):
    parts = []

    def walk(part):
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")

        if mime_type == "text/plain" and body_data:
            decoded = base64.urlsafe_b64decode(
                body_data + "=" * (-len(body_data) % 4)
            )
            parts.append(decoded.decode("utf-8", errors="replace"))

        for child in part.get("parts", []):
            walk(child)

    walk(payload)
    return "\n".join(parts).strip()


def get_header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def classify_email(subject, content):
    text = f"{subject} {content}".lower()

    marketing_keywords = [
        "newsletter", "special offer", "promotion",
        "register today", "exhibition", "webinar",
        "discount", "subscribe", "marketing"
    ]

    sales_keywords = [
        "quotation", "quote", "rental", "enquiry",
        "inquiry", "purchase order", "po-",
        "excavator", "crane", "availability"
    ]

    if any(keyword in text for keyword in marketing_keywords):
        return "marketing"

    if any(keyword in text for keyword in sales_keywords):
        return "sales"

    return "other"


def import_gmail_messages(query=DEFAULT_QUERY, max_results=MAX_MESSAGES):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A valid Gmail search query is required.")

    max_results = min(max(int(max_results), 1), MAX_MESSAGES)

    service = get_gmail_service()

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = response.get("messages", [])

    conn = get_connection()
    imported = 0
    skipped = 0

    try:
        with conn.cursor() as cur:
            for message_ref in messages:
                message = service.users().messages().get(
                    userId="me",
                    id=message_ref["id"],
                    format="full"
                ).execute()

                payload = message.get("payload", {})
                headers = payload.get("headers", [])

                sender_raw = get_header(headers, "From")
                sender_name, sender_email = parseaddr(sender_raw)

                subject = get_header(headers, "Subject") or "(No subject)"

                timestamp = message.get("internalDate")
                email_date = (
                    datetime.fromtimestamp(
                        int(timestamp) / 1000,
                        tz=timezone.utc
                    )
                    if timestamp else None
                )

                content = decode_body(payload) or message.get("snippet", "")
                category = classify_email(subject, content)

                cur.execute("""
                    INSERT INTO communications
                    (
                        organization_id, source, source_id,
                        sender, subject, content, timestamp, category
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (organization_id, source, source_id)
                    DO NOTHING
                    RETURNING id
                """, (
                    ORG_ID,
                    "gmail",
                    message["id"],
                    sender_email or sender_raw,
                    subject,
                    content,
                    email_date,
                    category
                ))

                if cur.fetchone():
                    imported += 1
                else:
                    skipped += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "matched": len(messages),
        "imported": imported,
        "skipped_duplicates": skipped,
        "query": query
    }
