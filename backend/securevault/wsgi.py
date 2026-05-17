"""
WSGI entry point for SecureVault.
Run with:  flask --app wsgi:app run  (dev)
           gunicorn wsgi:app          (prod)
"""
import os
from app.core.factory import create_app

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    app.run()