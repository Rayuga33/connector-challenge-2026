
import os
import hmac
from functools import wraps

from dotenv import load_dotenv

# Load environment variables before importing application modules.
load_dotenv()

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    session
)

from src.connectors.gmail_service import get_connected_account
from src.connectors.gmail_importer import import_gmail_messages

from src.services.analytics import (
    get_dashboard_metrics,
    get_monthly_rental_data,
    get_equipment_data,
    get_top_equipment
)

from src.services.query_engine import answer_question

from src.connectors.gmail_auth import (
    get_authorization_url,
    complete_oauth,
    is_gmail_connected,
    REDIRECT_URI
)


# -------------------------
# Flask configuration
# -------------------------

app = Flask(__name__)

app.secret_key = os.environ["FLASK_SECRET_KEY"]

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RENDER_EXTERNAL_HOSTNAME"))
)

DEMO_USERNAME = os.getenv("DEMO_USERNAME", "")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")


# -------------------------
# Authentication
# -------------------------

def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("authenticated"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required"
                }), 401

            return redirect("/login")

        return function(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("authenticated"):
        return redirect("/")

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        valid_username = (
            bool(DEMO_USERNAME)
            and hmac.compare_digest(username, DEMO_USERNAME)
        )

        valid_password = (
            bool(DEMO_PASSWORD)
            and hmac.compare_digest(password, DEMO_PASSWORD)
        )

        if valid_username and valid_password:
            session.clear()
            session["authenticated"] = True
            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------------
# Dashboard
# -------------------------

@app.route("/")
@login_required
def dashboard():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "EquipIntel"
    })


@app.route("/api/dashboard")
@login_required
def dashboard_api():
    return jsonify({
        "metrics": get_dashboard_metrics(),
        "monthly": get_monthly_rental_data(),
        "categories": get_equipment_data(),
        "top_equipment": get_top_equipment()
    })


@app.route("/api/ask", methods=["POST"])
@login_required
def ask():

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "Please enter a question."
        }), 400

    result = answer_question(question)

    return jsonify({
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"]
    })


# -------------------------
# Gmail OAuth integration
# -------------------------

@app.route("/connect/gmail")
@login_required
def connect_gmail():

    try:
        authorization_url, state, code_verifier = get_authorization_url()

        session["oauth_state"] = state
        session["oauth_code_verifier"] = code_verifier

        return redirect(authorization_url)

    except Exception:
        app.logger.exception("Could not start Gmail OAuth")

        return jsonify({
            "error": "Could not start Gmail connection."
        }), 500


@app.route("/auth/google/callback")
def google_callback():

    if request.args.get("error"):
        return jsonify({
            "error": "Google authorization was not completed.",
            "details": request.args.get("error")
        }), 400

    state = session.pop("oauth_state", None)
    code_verifier = session.pop("oauth_code_verifier", None)

    if not state or not code_verifier:
        return jsonify({
            "error": "OAuth session expired. Please connect again."
        }), 400

    try:
        callback_url = (
            REDIRECT_URI
            + "?"
            + request.query_string.decode("utf-8")
        )

        complete_oauth(
            state=state,
            authorization_response=callback_url,
            code_verifier=code_verifier
        )

        return """
            <h2>Gmail connected successfully!</h2>
            <p>EquipIntel has received Gmail read-only authorization.</p>
            <a href="/">Return to EquipIntel</a>
        """

    except Exception:
        app.logger.exception("Gmail OAuth callback failed")

        return jsonify({
            "error": "Gmail authorization failed. Check the server logs."
        }), 500


@app.route("/api/gmail/status")
@login_required
def gmail_status():

    return jsonify({
        "connected": is_gmail_connected()
    })


@app.route("/api/gmail/profile")
@login_required
def gmail_profile():

    try:
        account = get_connected_account()

        return jsonify({
            "connected": True,
            "account": account
        })

    except Exception:
        app.logger.exception("Could not retrieve Gmail profile")

        return jsonify({
            "connected": False,
            "error": "Could not retrieve Gmail profile."
        }), 500


@app.route("/api/gmail/import", methods=["POST"])
@login_required
def gmail_import():

    data = request.get_json(silent=True) or {}
    query = data.get("query", "newer_than:90d")

    try:
        result = import_gmail_messages(
            query=query,
            max_results=100
        )

        return jsonify({
            "success": True,
            **result
        })

    except Exception:
        app.logger.exception("Gmail import failed")

        return jsonify({
            "success": False,
            "error": "Gmail import failed. Check the server logs."
        }), 500


# -------------------------
# Application entry point
# -------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        debug=True,
        port=5000
    )
