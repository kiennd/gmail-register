@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Move to project root
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%\..

REM Python
set PYTHON=python

REM Create venv if missing
if not exist .venv (
  echo [setup] Creating virtual environment (.venv)
  %PYTHON% -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
pip install -U pip >nul
pip install -r requirements.txt

REM Ensure Camoufox browser is available (no-op if already fetched)
python -m camoufox fetch

REM Run project
python register_gmail.py --config config.json %*
endlocal 