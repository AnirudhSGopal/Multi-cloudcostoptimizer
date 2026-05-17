@echo off
:: Start the Celery worker for SecureVault (Windows)
:: Run from the securevault\ root directory with .venv active.

echo Starting SecureVault Celery worker...
call .venv\Scripts\activate.bat
celery -A wsgi.celery worker --loglevel=info --pool=solo