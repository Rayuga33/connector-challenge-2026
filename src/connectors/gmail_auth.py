
import os
import json

from cryptography.fernet import Fernet, InvalidToken
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

from src.database.db import get_connection

load_dotenv()

ORG_ID = "a94a6421-0db0-40f2-850a-7e6ba623eff0"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:5000/auth/google/callback"
)

# Allow HTTP only for local development.
if REDIRECT_URI.startswith("http://"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
else:
    os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)


def get_fernet():
    key = os.getenv("GMAIL_TOKEN_ENCRYPTION_KEY")

    if not key:
        raise RuntimeError(
            "GMAIL_TOKEN_ENCRYPTION_KEY is missing."
        )

    return Fernet(key.encode())


def get_google_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Google OAuth client environment variables are missing."
        )

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }


def create_oauth_flow(
    state=None,
    code_verifier=None,
    autogenerate_code_verifier=False
):
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier
    )

    flow.redirect_uri = REDIRECT_URI

    return flow


def get_authorization_url():
    flow = create_oauth_flow(
        autogenerate_code_verifier=True
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return authorization_url, state, flow.code_verifier


def save_gmail_credentials(credentials):
    encrypted_token = get_fernet().encrypt(
        credentials.to_json().encode("utf-8")
    ).decode("utf-8")

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO gmail_oauth_tokens
                    (organization_id, encrypted_token, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (organization_id)
                DO UPDATE SET
                    encrypted_token = EXCLUDED.encrypted_token,
                    updated_at = NOW()
            """, (ORG_ID, encrypted_token))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_gmail_credentials():
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT encrypted_token
                FROM gmail_oauth_tokens
                WHERE organization_id = %s
            """, (ORG_ID,))

            row = cur.fetchone()

    finally:
        conn.close()

    if not row:
        return None

    try:
        decrypted = get_fernet().decrypt(
            row["encrypted_token"].encode("utf-8")
        )

        token_data = json.loads(decrypted.decode("utf-8"))

        return Credentials.from_authorized_user_info(
            token_data,
            SCOPES
        )

    except (InvalidToken, ValueError, json.JSONDecodeError):
        raise RuntimeError(
            "Stored Gmail credentials could not be decrypted. "
            "Check the encryption key."
        )


def complete_oauth(state, authorization_response, code_verifier):
    if not code_verifier:
        raise ValueError("OAuth code verifier is missing.")

    flow = create_oauth_flow(
        state=state,
        code_verifier=code_verifier
    )

    flow.fetch_token(
        authorization_response=authorization_response
    )

    save_gmail_credentials(flow.credentials)

    return True


def is_gmail_connected():
    credentials = get_gmail_credentials()

    return (
        credentials is not None
        and (
            credentials.valid
            or bool(credentials.refresh_token)
        )
    )
