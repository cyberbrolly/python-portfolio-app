from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import time

from flask import Flask, redirect, request, send_from_directory

app = Flask(__name__)

DB_FILE = Path("database.db")
MAX_SUBMISSIONS_PER_WINDOW = 5
RATE_LIMIT_WINDOW_SECONDS = 10 * 60
MIN_SECONDS_BETWEEN_SUBMISSIONS = 8
ip_submissions: dict[str, list[float]] = {}


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            ip TEXT NOT NULL,
            handle TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _is_rate_limited(ip: str, now: float) -> bool:
    timestamps = ip_submissions.get(ip, [])
    valid_after = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = [ts for ts in timestamps if ts >= valid_after]

    if timestamps and now - timestamps[-1] < MIN_SECONDS_BETWEEN_SUBMISSIONS:
        ip_submissions[ip] = timestamps
        return True

    if len(timestamps) >= MAX_SUBMISSIONS_PER_WINDOW:
        ip_submissions[ip] = timestamps
        return True

    timestamps.append(now)
    ip_submissions[ip] = timestamps
    return False


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/styles.css")
def styles():
    return send_from_directory(".", "styles.css")


@app.route("/messages")
def messages():
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, timestamp_utc, ip, handle, email, message
        FROM messages
        ORDER BY id DESC
        """
    )
    data = cursor.fetchall()
    conn.close()

    if not data:
        return "No messages yet."

    rows = []
    for row in data:
        rows.append(
            f"[{row['id']}] {row['timestamp_utc']} | {row['handle']} <{row['email']}> ({row['ip']}): {row['message']}"
        )

    return "<br>".join(rows)


@app.post("/contact")
def contact():
    # Honeypot field: bots often fill hidden inputs.
    if request.form.get("company", "").strip():
        return redirect("/", code=303)

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    now = time.time()
    if _is_rate_limited(ip, now):
        return "Too many submissions. Please wait and try again.", 429

    handle = request.form.get("handle", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not handle or not email or not message:
        return "Missing required fields.", 400

    if "@" not in email:
        return "Please provide a valid email address.", 400

    if len(handle) > 80 or len(email) > 254 or len(message) > 2000:
        return "Input is too long.", 400

    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (timestamp_utc, ip, handle, email, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            ip,
            handle,
            email,
            message,
        ),
    )
    conn.commit()
    conn.close()

    return redirect("/", code=303)


if __name__ == "__main__":
    _init_db()
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
