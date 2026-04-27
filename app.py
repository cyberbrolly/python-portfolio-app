import csv
from datetime import datetime, timezone
from pathlib import Path
import time

from flask import Flask, redirect, request, send_from_directory

app = Flask(__name__)

DATA_FILE = Path("contact_messages.csv")
MAX_SUBMISSIONS_PER_WINDOW = 5
RATE_LIMIT_WINDOW_SECONDS = 10 * 60
MIN_SECONDS_BETWEEN_SUBMISSIONS = 8
ip_submissions: dict[str, list[float]] = {}


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

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not DATA_FILE.exists()

    with DATA_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new_file:
            writer.writerow(["timestamp_utc", "ip", "handle", "email", "message"])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            ip,
            handle,
            email,
            message,
        ])

    return redirect("/", code=303)


if __name__ == "__main__":
    app.run(debug=True)
