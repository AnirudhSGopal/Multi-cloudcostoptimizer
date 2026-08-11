import pytest
from app.core.factory import create_app
from app.core.extensions import db
from app.models.user import User, RoleEnum
from app.models.cloud_account import CloudAccount, AccountStatusEnum
from app.models.cloud import CloudMetric, CloudProviderEnum
from app.models.scan import ScanJob, ScanStatusEnum


import os
os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

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


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(username="admin_test", email="admin_test@cloudopt.ai", role=RoleEnum.ADMIN, is_active=True)
        admin.password = "adminpass123"
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def viewer_user(app):
    with app.app_context():
        viewer = User(username="viewer_test", email="viewer_test@cloudopt.ai", role=RoleEnum.VIEWER, is_active=True)
        viewer.password = "viewerpass123"
        db.session.add(viewer)
        db.session.commit()
        return viewer.id


def get_token(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"username": email, "password": password})
    return resp.get_json()["access_token"]


def test_non_admin_gets_403(client, viewer_user):
    token = get_token(client, "viewer_test@cloudopt.ai", "viewerpass123")
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/users/1"),
        ("PATCH", "/api/v1/admin/users/1"),
        ("DELETE", "/api/v1/admin/users/1?confirm=true"),
        ("GET", "/api/v1/admin/cloud-accounts"),
        ("GET", "/api/v1/admin/scans"),
        ("GET", "/api/v1/admin/stats"),
        ("GET", "/api/v1/admin/system-health"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            res = client.get(endpoint, headers=headers)
        elif method == "PATCH":
            res = client.patch(endpoint, headers=headers, json={})
        elif method == "DELETE":
            res = client.delete(endpoint, headers=headers)
        assert res.status_code == 403, f"Expected 403 for {endpoint}, got {res.status_code}"


def test_admin_routes(client, app, admin_user, viewer_user):
    token = get_token(client, "admin_test@cloudopt.ai", "adminpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # GET /users
    res = client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 2

    # GET /users/<id>
    res = client.get(f"/api/v1/admin/users/{viewer_user}", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["user"]["username"] == "viewer_test"

    # PATCH /users/<id> (Role change & disable)
    res = client.patch(f"/api/v1/admin/users/{viewer_user}", headers=headers, json={"role": "analyst", "is_active": False})
    assert res.status_code == 200
    assert res.get_json()["user"]["role"] == "analyst"
    assert res.get_json()["user"]["is_active"] is False

    # Confirm disabled user cannot login
    disabled_resp = client.post("/api/v1/auth/login", json={"username": "viewer_test@cloudopt.ai", "password": "viewerpass123"})
    assert disabled_resp.status_code == 403

    # Re-enable user
    client.patch(f"/api/v1/admin/users/{viewer_user}", headers=headers, json={"is_active": True})

    # GET /cloud-accounts
    res = client.get("/api/v1/admin/cloud-accounts", headers=headers)
    assert res.status_code == 200

    # GET /scans
    res = client.get("/api/v1/admin/scans", headers=headers)
    assert res.status_code == 200

    # GET /stats
    res = client.get("/api/v1/admin/stats", headers=headers)
    assert res.status_code == 200
    stats = res.get_json()
    assert stats["total_users"] == 2

    # GET /system-health
    res = client.get("/api/v1/admin/system-health", headers=headers)
    assert res.status_code == 200
    health = res.get_json()
    assert "checks" in health


def test_user_deletion_cascade(client, app, admin_user):
    with app.app_context():
        target = User(username="target_user", email="target@cloudopt.ai", role=RoleEnum.VIEWER)
        target.password = "targetpass"
        db.session.add(target)
        db.session.commit()

        acc = CloudAccount(user_id=target.id, provider=CloudProviderEnum.AWS, account_label="Test AWS", encrypted_credentials="mock")
        db.session.add(acc)
        db.session.commit()

        scan = ScanJob(repo_url="https://github.com/example/repo", requested_by=target.id, status=ScanStatusEnum.COMPLETED)
        db.session.add(scan)
        db.session.commit()

        metric = CloudMetric(user_id=target.id, provider=CloudProviderEnum.AWS, cloud_account_id=acc.id, size_bytes=100)
        db.session.add(metric)
        db.session.commit()

        target_id = target.id
        acc_id = acc.id
        scan_id = scan.id
        metric_id = metric.id

    token = get_token(client, "admin_test@cloudopt.ai", "adminpass123")
    headers = {"Authorization": f"Bearer {token}"}

    # Delete user with confirm=true
    res = client.delete(f"/api/v1/admin/users/{target_id}?confirm=true", headers=headers)
    assert res.status_code == 200

    with app.app_context():
        assert User.query.get(target_id) is None
        assert CloudAccount.query.get(acc_id) is None
        assert ScanJob.query.get(scan_id) is None
        assert CloudMetric.query.get(metric_id) is None
