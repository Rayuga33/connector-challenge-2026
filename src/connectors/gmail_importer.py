import base64
import re
from datetime import datetime, timezone
from email.utils import parseaddr

from src.connectors.gmail_service import get_gmail_service
from src.database.db import get_connection


DEFAULT_QUERY = "newer_than:90d"
MAX_MESSAGES = 100


def decode_body(payload):
    """Extract readable plain-text email content."""
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

    if not parts:
        snippet = ""
        return snippet

    return "\n".join(parts).strip()


def get_header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def classify_email(subject, content):
    text = f"{subject} {content}".lower()

    sales_keywords = [
        "quotation", "quote", "rental", "enquiry", "inquiry",
        "purchase order", "po-", "invoice", "payment",
        "excavator", "crane", "equipment", "availability"
    ]

    marketing_keywords = [
        "newsletter", "special offer", "promotion",
        "register today", "exhibition", "webinar",
        "discount", "subscribe", "marketing"
    ]

    if any(keyword in text for keyword in sales_keywords):
        return "sales"

    if any(keyword in text for keyword in marketing_keywords):
        return "marketing"

    return "other"


def import_gmail_messages(query=DEFAULT_QUERY, max_results=MAX_MESSAGES):
    """Import matching Gmail messages into communications."""
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
            if timestamp:
                email_date = datetime.fromtimestamp(
                    int(timestamp) / 1000,
                    tz=timezone.utc
                ).isoformat()
            else:
                email_date = None

            content = decode_body(payload)

            if not content:
                content = message.get("snippet", "")

            category = classify_email(subject, content)

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO communications
                (source, source_id, sender, subject, content, timestamp, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "gmail",
                    message["id"],
                    sender_email or sender_raw,
                    subject,
                    content,
                    email_date,
                    category
                )
            )

            if cursor.rowcount:
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