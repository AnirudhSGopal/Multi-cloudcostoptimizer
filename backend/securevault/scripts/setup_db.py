"""
Run once to create all PostgreSQL tables.

Usage:
    python scripts/setup_db.py
"""
import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.factory import create_app
from app.core.extensions import db

# Import all models so SQLAlchemy knows about them
from app.models import user, scan, cloud  # noqa: F401

def main():
    env = os.getenv("FLASK_ENV", "development")
    app = create_app(env)
    with app.app_context():
        db.create_all()
        print("✅  All tables created successfully.")
        print("    Tables:", list(db.engine.table_names()) if hasattr(db.engine, 'table_names') else "done")

if __name__ == "__main__":
    main()