# 50thCAM Kiosk App

Flask application for Raspberry Pi that captures from a USB-connected Canon camera and generates:

- `original-xxxxx.jpg`
- `originalW-xxxxx.jpg`
- `1976edition-xxxxx.jpg`
- `social-xxxxx.jpg`

## Features

- Kiosk page with live-ish camera preview (refreshing `/preview.jpg` every 1.5 seconds)
- Capture endpoint that shells out to `gphoto2`
- Image pipeline with watermark, retro filter, and social composite in `2868x1320`
- Send flow that emails the three generated images (`originalW`, `1976edition`, `social`)
- Basic UI/JS kept intentionally old-browser friendly for Safari 4.1.3-era environments

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install camera dependencies on Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install -y gphoto2
```

Place required artwork in `assets/`:

- `assets/Steve.jpg`
- `assets/Frame.jpg`

## Run

```bash
python3 app.py
```

Open `http://<pi-ip>:8080`.

## Email configuration

Set environment variables before launch:

- `SMTP_HOST`
- `SMTP_PORT` (optional, default `587`)
- `SMTP_USER` (optional if relay allows anonymous)
- `SMTP_PASS` (optional)
- `MAIL_FROM` (optional; falls back to `SMTP_USER`)

Optional watermark text:

- `WATERMARK_TEXT` (default: `50thCAM`)
