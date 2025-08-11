#!/usr/bin/env bash
set -euo pipefail

# Move to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/bin}"
cd "$PROJECT_ROOT"

# Python
PYTHON_BIN="python3"

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "[setup] Creating virtual environment (.venv)"
  "$PYTHON_BIN" -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install dependencies
pip install -U pip >/dev/null
pip install -r requirements.txt

# Ensure Camoufox browser is available (no-op if already fetched)
python -m camoufox fetch

# Run project
exec python register_gmail.py --config config.json "$@" 