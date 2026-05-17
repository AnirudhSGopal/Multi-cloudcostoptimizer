@echo off
:: Start the Flask development server for SecureVault (Windows)
:: Run from the securevault\ root directory.

echo Starting SecureVault Flask server...
call .venv\Scripts\activate.bat
flask --app wsgi:app run --debug