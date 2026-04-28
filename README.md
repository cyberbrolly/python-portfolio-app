# Cyberbrolly Portfolio

Single-page cyberpunk portfolio with a lightweight Flask backend for contact form handling.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Deploy on Render

This repo includes `render.yaml` for one-click deployment.

### Option A: Blueprint (recommended)
1. Push this repo to GitHub.
2. In Render, choose **New +** → **Blueprint**.
3. Select your repo.
4. Render reads `render.yaml` and creates the web service automatically.

### Option B: Manual web service
1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `gunicorn app:app`
3. Set runtime to **Python**.

## Contact form backend

- Endpoint: `POST /contact`
- Read messages: `GET /messages`
- Spam protection: honeypot + IP rate limiting + submission cooldown
- Storage: `database.db` SQLite file (created automatically)
