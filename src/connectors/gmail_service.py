from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from src.connectors.gmail_auth import (
    get_gmail_credentials,
    TOKEN_FILE
)


def get_gmail_service():
    credentials = get_gmail_credentials()

    if credentials is None:
        raise Exception("Gmail is not connected. Please authorize first.")

    # Refresh expired credentials when possible
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    if not credentials.valid:
        raise Exception("Gmail authorization is expired. Please reconnect.")

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False
    )


def get_connected_account():
    service = get_gmail_service()

    profile = service.users().getProfile(
        userId="me"
    ).execute()

    return {
        "email": profile.get("emailAddress"),
        "total_messages": profile.get("messagesTotal", 0),
        "total_threads": profile.get("threadsTotal", 0)
    }