import csv
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, redirect, request, send_from_directory

app = Flask(__name__)

DATA_FILE = Path("contact_messages.csv")


@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/styles.css")
def styles():
    return send_from_directory(".", "styles.css")


@app.post("/contact")
def contact():
    handle = request.form.get("handle", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not handle or not email or not message:
        return "Missing required fields.", 400

    if "@" not in email:
        return "Please provide a valid email address.", 400

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not DATA_FILE.exists()

    with DATA_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new_file:
            writer.writerow(["timestamp_utc", "handle", "email", "message"])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            handle,
            email,
            message,
        ])

    return redirect("/", code=303)


if __name__ == "__main__":
    app.run(debug=True)
