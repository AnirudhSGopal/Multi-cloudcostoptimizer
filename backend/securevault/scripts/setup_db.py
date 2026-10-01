"""Apply the database migrations to the configured database."""
import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.factory import create_app
from flask_migrate import upgrade

def main():
    env = os.getenv("FLASK_ENV", "development")
    app = create_app(env)
    with app.app_context():
        upgrade()
        print("[OK] Database migrations applied successfully.")

if __name__ == "__main__":
    main()