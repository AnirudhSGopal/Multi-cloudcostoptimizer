import os
import pytest

os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

from app.core.factory import create_app
from app.core.extensions import db
from app.models.user import User, RoleEnum


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_ignores_role_admin_privilege_escalation(client, app):
    """
    Regression Test:
    Attempting to self-register with role="admin" or role="analyst" in the request body
    MUST be ignored. The user MUST be created with RoleEnum.VIEWER.
    """
    payload = {
        "username": "attacker",
        "email": "attacker@example.com",
        "password": "AttackerPassword123!",
        "role": "admin"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()

    # Response user object must show role viewer, NOT admin
    assert data["user"]["role"] == RoleEnum.VIEWER.value

    # DB record must show role viewer, NOT admin
    with app.app_context():
        user = User.query.filter_by(email="attacker@example.com").first()
        assert user is not None
        assert user.role == RoleEnum.VIEWER
        assert user.role != RoleEnum.ADMIN
