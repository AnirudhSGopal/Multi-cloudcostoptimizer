import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

import tempfile
from pathlib import Path
import pytest
from flask_jwt_extended import create_access_token

from app.core.factory import create_app
from app.core.extensions import db
from app.services.scanner.static_analyzer import analyze_repository

@pytest.fixture
def app():
    # Spin up Flask app with in-memory testing configuration
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "testing-jwt-secret-key"
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="admin")
        return {"Authorization": f"Bearer {token}"}

def test_static_analyzer_rules():
    """Verify that analyze_repository correctly detects insecure patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test python file with vulnerability patterns
        test_file = Path(temp_dir) / "vulnerable_app.py"
        test_file.write_text("""
def run_app():
    # SEC001 - AWS Access Key ID
    aws_key = "AKIA1234567890ABCDEF"
    
    # CODE001 - eval
    eval("print('hello')")
    
    # CODE014 - Hardcoded password
    db_password = "supersecretpassword123"
    
    return aws_key
""", encoding="utf-8")

        findings, stats = analyze_repository(temp_dir)

        assert stats.files_scanned == 1
        assert len(findings) >= 3

        rule_ids = {f["rule_id"] for f in findings}
        assert "SEC001" in rule_ids
        assert "CODE001" in rule_ids
        assert "CODE014" in rule_ids

def test_api_audit_endpoint(client, auth_headers):
    """Verify that the POST /api/audit endpoint runs rule-based analysis and returns merged findings."""
    payload = {
        "repoUrl": None,
        "files": [
            {
                "name": "app.py",
                "content": """
def check():
    eval("1 + 1")
    key = "AKIA1234567890ABCDEF"
"""
            }
        ]
    }

    # Make post request to /api/audit
    response = client.post("/api/audit", json=payload, headers=auth_headers)
    assert response.status_code == 200

    data = response.get_json()
    assert "overall" in data
    assert "alerts" in data
    assert "compliance" in data

    # Verify that the overall score is reduced and status is updated based on our findings
    score = data["overall"]["score"]
    status = data["overall"]["status"]
    assert score < 100
    assert status in ("Critical", "Moderate")

    # Find the rule-based alerts in the response
    alerts = data["alerts"]
    rb_alerts = [a for a in alerts if a["id"].startswith("rb-")]
    assert len(rb_alerts) >= 2

    # Check for SEC001 and CODE001
    messages = [a["message"].lower() for a in rb_alerts]
    assert any("aws access key" in m or "sec001" in m for m in messages)
    assert any("eval" in m or "code001" in m for m in messages)
