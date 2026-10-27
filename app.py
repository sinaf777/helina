import hmac
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "registrations.db")))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "")
if not app.secret_key:
    raise RuntimeError("Set FLASK_SECRET_KEY before starting the app. See README.txt.")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                bank_account_number TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


def verify_csrf():
    expected = session.get("csrf_token", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        abort(403, description="Invalid or expired form token. Please go back and try again.")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        verify_csrf()
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        account = "".join(request.form.get("bank_account_number", "").split()).replace("-", "")

        if not 2 <= len(full_name) <= 120:
            flash("Please enter your full name. / እባክዎ ሙሉ ስምዎን ያስገቡ።", "error")
        elif not 7 <= len(phone) <= 25:
            flash("Please enter a valid phone number. / እባክዎ ትክክለኛ ስልክ ቁጥር ያስገቡ።", "error")
        elif not (6 <= len(account) <= 34 and account.isdigit()):
            flash("Please enter a valid account number. / እባክዎ ትክክለኛ የሂሳብ ቁጥር ያስገቡ።", "error")
        else:
            with get_db() as db:
                db.execute(
                    "INSERT INTO registrations (full_name, phone, bank_account_number) VALUES (?, ?, ?)",
                    (full_name, phone, account),
                )
            flash("Registration submitted successfully. / ምዝገባዎ በተሳካ ሁኔታ ተልኳል።", "success")
            return redirect(url_for("register"))
    return render_template("register.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
        return render_template("admin_setup.html"), 503

    if request.method == "POST":
        verify_csrf()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if hmac.compare_digest(username, ADMIN_USERNAME) and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["admin_logged_in"] = True
            session["csrf_token"] = secrets.token_urlsafe(32)
            next_path = request.args.get("next", "")
            # Only allow local relative paths to prevent open redirects.
            if not next_path.startswith("/") or next_path.startswith("//") or urlparse(next_path).netloc:
                next_path = url_for("admin_dashboard")
            return redirect(next_path)
        flash("Invalid username or password. / የተሳሳተ የተጠቃሚ ስም ወይም የይለፍ ቃል።", "error")
    return render_template("admin_login.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    q = request.args.get("q", "").strip()[:100]
    with get_db() as db:
        if q:
            records = db.execute(
                """SELECT id, full_name, phone, bank_account_number, created_at
                   FROM registrations WHERE full_name LIKE ? OR phone LIKE ? ORDER BY id DESC""",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            records = db.execute(
                "SELECT id, full_name, phone, bank_account_number, created_at FROM registrations ORDER BY id DESC"
            ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    return render_template("admin_dashboard.html", registrations=records, total=total, q=q)


@app.post("/admin/delete/<int:record_id>")
@admin_required
def delete_registration(record_id):
    verify_csrf()
    with get_db() as db:
        db.execute("DELETE FROM registrations WHERE id = ?", (record_id,))
    flash("Registration deleted. / ምዝገባው ተሰርዟል።", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/logout")
@admin_required
def admin_logout():
    verify_csrf()
    session.clear()
    return redirect(url_for("admin_login"))


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, message=getattr(error, "description", "Forbidden")), 403


init_db()

if __name__ == "__main__":
    # Local development only; use a production WSGI server when deploying online.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
