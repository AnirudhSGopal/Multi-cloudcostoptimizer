from app.core import factory
from app.core.factory import create_app


def test_health_remains_liveness_while_ready_checks_dependencies(monkeypatch):
    app = create_app("testing")
    monkeypatch.setattr(factory, "_database_is_ready", lambda: True)
    monkeypatch.setattr(factory, "_redis_is_ready", lambda: False)
    client = app.test_client()

    assert client.get("/health").status_code == 200

    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {
        "status": "not_ready",
        "checks": {"database": "ok", "redis": "unavailable"},
    }


def test_ready_returns_success_only_when_database_and_redis_are_healthy(monkeypatch):
    app = create_app("testing")
    monkeypatch.setattr(factory, "_database_is_ready", lambda: True)
    monkeypatch.setattr(factory, "_redis_is_ready", lambda: True)

    response = app.test_client().get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok"},
    }
