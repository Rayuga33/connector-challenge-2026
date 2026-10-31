import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

import json
from pathlib import Path

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials


BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

REDIRECT_URI = "http://127.0.0.1:5000/auth/google/callback"


def create_oauth_flow(
    state=None,
    code_verifier=None,
    autogenerate_code_verifier=False
):
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json was not found in the project root."
        )

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
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
        include_granted_scopes="false",
        prompt="consent"
    )

    return authorization_url, state, flow.code_verifier


def complete_oauth(state, authorization_response, code_verifier):
    if not code_verifier:
        raise ValueError("OAuth code verifier is missing. Restart authorization.")

    flow = create_oauth_flow(
        state=state,
        code_verifier=code_verifier
    )

    flow.fetch_token(
        authorization_response=authorization_response
    )

    credentials = flow.credentials

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8"
    )

    return True


def get_gmail_credentials():
    if not TOKEN_FILE.exists():
        return None

    try:
        return Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES
        )
    except (ValueError, json.JSONDecodeError):
        return None


def is_gmail_connected():
    credentials = get_gmail_credentials()
    return credentials is not None and credentials.valid