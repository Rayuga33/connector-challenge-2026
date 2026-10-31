
import os
from dotenv import load_dotenv

# Load environment variables from .env
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
    is_gmail_connected
)


app = Flask(__name__)

# Persistent session security
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "EquipIntel"
    })


@app.route("/api/dashboard")
def dashboard_api():
    return jsonify({
        "metrics": get_dashboard_metrics(),
        "monthly": get_monthly_rental_data(),
        "categories": get_equipment_data(),
        "top_equipment": get_top_equipment()
    })


@app.route("/api/ask", methods=["POST"])
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
        complete_oauth(
            state=state,
            authorization_response=request.url,
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
            "error": "Gmail authorization failed. Check the server terminal."
        }), 500


@app.route("/api/gmail/status")
def gmail_status():
    return jsonify({
        "connected": is_gmail_connected()
    })


@app.route("/api/gmail/profile")
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
            "error": "Gmail import failed. Check the server terminal."
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        debug=True,
        port=5000
    )
