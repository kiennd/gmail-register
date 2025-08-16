# Gmail Register with Multiple Engines (Python)

Automates the initial steps of creating a Gmail account using multiple browser automation engines:

- **Hidemium**: Local/cloud profile management with anti-detection
- **GoLogin**: Cloud-based profile management with advanced fingerprinting
- **Camoufox**: Stealth Firefox + Playwright (fallback)

This assists with form filling and navigation, then pauses for manual steps like SMS verification and CAPTCHA/Terms.

Important: Automating account creation may violate Google Terms of Service. Use only for legitimate, permitted purposes and your own accounts. No CAPTCHA solving is included.

## Prerequisites
- Python 3.10+
- Sufficient disk space for browser downloads
- GoLogin account (if using GoLogin engine)
- Hidemium installation (if using Hidemium engine)

## Setup

### 1. Clone and setup environment
```bash
git clone <repository-url>
cd gmail-register
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 2. Choose your engine

#### Option A: Hidemium (Local/Cloud)
```bash
# Install Hidemium locally
# Download from: https://hidemium.io/
# Or use cloud version
```

#### Option B: GoLogin (Cloud)
```bash
# Get access token from: https://app.gologin.com/settings/api
# Add to config.json or .env
```

#### Option C: Camoufox (Fallback)
```bash
python -m camoufox fetch
```

### 3. Configure environment
```bash
# Copy and edit configuration
cp env.example .env
# Edit .env with your engine choice and settings
```

## Run

### Basic usage
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python register_gmail.py \
  --first-name "$FIRST_NAME" \
  --last-name "$LAST_NAME" \
  --username "$GMAIL_USERNAME" \
  --password "$GMAIL_PASSWORD"
```

### Engine-specific examples

#### Hidemium
```bash
# Set engine in config.json or .env
echo '{"ENGINE": "hidemium"}' > config.json
python register_gmail.py
```

#### GoLogin
```bash
# Set engine and token in config.json or .env
echo '{"ENGINE": "gologin", "GOLOGIN_ACCESS_TOKEN": "your_token"}' > config.json
python register_gmail.py
```

#### Camoufox (fallback)
```bash
# Set engine in config.json or .env
echo '{"ENGINE": "camoufox"}' > config.json
python register_gmail.py
```

### Configuration options
- `--headless [true|false|virtual]` default from config
- `--debug` verbose logging
- `--proxy PROXY_URL` overrides config proxy settings

## What it does
- Launches browser with stealth fingerprints and optional proxy/GeoIP
- Opens Google account sign-up and fills first page fields
- Optionally fills phone, recovery email if provided
- Pauses for manual verification (SMS, CAPTCHA, Terms)

## Examples and Testing

### Test GoLogin functionality
```bash
python examples/gologin_example.py
```

### Test Gmail registration with GoLogin
```bash
python examples/gologin_gmail_register_example.py
```

### Test Hidemium functionality
```bash
python examples/complete_hidemium_flow.py
```

## Notes
- Google frequently changes selectors; this script targets stable `name` attributes where possible
- Phone/SMS, CAPTCHA, and Terms cannot be automated here; follow on-screen instructions when prompted
- Profiles are managed by the selected engine (Hidemium/GoLogin/Camoufox)

## Documentation
- [GoLogin Setup Guide](GOLOGIN_SETUP.md) - Complete GoLogin setup and usage
- [Hidemium Setup Guide](HIDEMIUM_SETUP.md) - Complete Hidemium setup and usage

## Uninstall
```bash
# Camoufox browser
rm -rf ~/.cache/camoufox ~/.local/share/camoufox ~/.camoufox

# Hidemium (local installation)
# Remove from your system manually

# GoLogin (cloud-based, no local files to remove)
``` # gmail-register
