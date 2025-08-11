# Gmail Register with Camoufox (Python)

Automates the initial steps of creating a Gmail account using Camoufox (stealth Firefox + Playwright). This assists with form filling and navigation, then pauses for manual steps like SMS verification and CAPTCHA/Terms.

Important: Automating account creation may violate Google Terms of Service. Use only for legitimate, permitted purposes and your own accounts. No CAPTCHA solving is included.

## Prerequisites
- macOS with Python 3.10+
- Sufficient disk space for Camoufox browser download

## Setup
```bash
cd /Users/kiennguyenduc/Working/gmail-register
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python -m camoufox fetch
```

Create environment config:
```bash
# If .env.example exists (preferred), otherwise copy env.example
[ -f .env.example ] && cp .env.example .env || cp env.example .env
# edit .env with your details
```

## Run
```bash
source .venv/bin/activate
python register_gmail.py \
  --first-name "$FIRST_NAME" \
  --last-name "$LAST_NAME" \
  --username "$GMAIL_USERNAME" \
  --password "$GMAIL_PASSWORD"
```

Or rely on `.env` values only:
```bash
python register_gmail.py
```

Optional flags:
- `--headless [true|false|virtual]` default from `.env` (false)
- `--debug` verbose logging
- `--proxy PROXY_URL` overrides `.env` `PROXY_URL`

## What it does
- Launches Camoufox with stealth fingerprints and optional proxy/GeoIP
- Opens Google account sign-up and fills first page fields
- Optionally fills phone, recovery email if provided
- Pauses for manual verification (SMS, CAPTCHA, Terms)

## Notes
- Google frequently changes selectors; this script targets stable `name` attributes where possible
- Phone/SMS, CAPTCHA, and Terms cannot be automated here; follow on-screen instructions when prompted
- A persistent profile is saved in `profiles/` if enabled

## Uninstall Camoufox browser
```bash
rm -rf ~/.cache/camoufox ~/.local/share/camoufox ~/.camoufox
``` # gmail-register
