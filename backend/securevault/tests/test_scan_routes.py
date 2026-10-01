import pytest
from contextlib import contextmanager
from types import SimpleNamespace
from flask_jwt_extended import create_access_token
from sqlalchemy import update

from app.core.extensions import db
from app.core.factory import create_app
from app.models.scan import ScanJob, ScanStatusEnum
from app.models.user import RoleEnum, User


@pytest.fixture
def scan_app(tmp_path):
    app = create_app("testing")
    app.config["CLONE_BASE_DIR"] = str(tmp_path)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _create_user_token(app, username, email):
    with app.app_context():
        user = User(username=username, email=email, role=RoleEnum.VIEWER)
        user.password = "scan-test-password"
        db.session.add(user)
        db.session.commit()
        return create_access_token(identity=str(user.id)), user.id


def test_start_scan_validates_url_persists_job_and_queues_task(scan_app, monkeypatch):
    token, user_id = _create_user_token(scan_app, "scan-owner", "scan-owner@example.test")
    queued = {}
    monkeypatch.setattr("app.api.v1.scan.routes._broker_is_ready", lambda: True)

    def queue_scan(job_id):
        queued["job_id"] = job_id
        return type("QueuedTask", (), {"id": "task-123"})()

    monkeypatch.setattr("app.api.v1.scan.routes.run_scan_task.delay", queue_scan)

    response = scan_app.test_client().post(
        "/api/v1/scan/start",
        json={
            "repo_url": "https://github.com/acme/service.git",
            "branch": "release/2026",
            "gemini_review": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    assert response.get_json()["scan"]["status"] == "pending"
    assert queued["job_id"] == response.get_json()["scan"]["id"]
    with scan_app.app_context():
        job = db.session.get(ScanJob, queued["job_id"])
        assert job.requested_by == user_id
        assert job.branch == "release/2026"
        assert job.gemini_review_requested is True
        assert job.celery_task_id == "task-123"


def test_start_scan_fails_fast_when_broker_is_unavailable(scan_app, monkeypatch):
    token, user_id = _create_user_token(
        scan_app, "scan-broker-down", "scan-broker-down@example.test"
    )
    monkeypatch.setattr("app.api.v1.scan.routes._broker_is_ready", lambda: False)
    monkeypatch.setattr(
        "app.api.v1.scan.routes.run_scan_task.delay",
        lambda job_id: pytest.fail("Do not enqueue when Redis is unavailable"),
    )

    response = scan_app.test_client().post(
        "/api/v1/scan/start",
        json={"repo_url": "https://github.com/acme/service"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "Scan queue unavailable. Confirm Redis and the Celery worker are running, "
        "then retry."
    )
    with scan_app.app_context():
        assert ScanJob.query.filter_by(requested_by=user_id).count() == 0


def test_start_scan_reports_unavailable_queue_without_waiting_for_results(
    scan_app, monkeypatch
):
    token, user_id = _create_user_token(
        scan_app, "scan-queue-down", "scan-queue-down@example.test"
    )

    def fail_to_queue(job_id):
        raise ConnectionError("broker connection failed")

    monkeypatch.setattr(
        "app.api.v1.scan.routes.run_scan_task.delay", fail_to_queue
    )
    monkeypatch.setattr("app.api.v1.scan.routes._broker_is_ready", lambda: True)

    response = scan_app.test_client().post(
        "/api/v1/scan/start",
        json={"repo_url": "https://github.com/acme/service"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "Scan queue unavailable. Confirm Redis and the Celery worker are running, "
        "then retry."
    )
    with scan_app.app_context():
        job = ScanJob.query.filter_by(requested_by=user_id).one()
        assert job.status == ScanStatusEnum.FAILED
        assert job.error_msg == "Unable to queue the scan."


def test_public_github_scan_runs_security_rules_and_returns_findings(scan_app, monkeypatch):
    token, _ = _create_user_token(
        scan_app, "scan-integration", "scan-integration@example.test"
    )

    def fake_clone(url, target, **kwargs):
        from pathlib import Path

        target_path = Path(target)
        target_path.mkdir(parents=True, exist_ok=True)
        (target_path / "unsafe.py").write_text(
            'result = eval(user_input)\naws_key = "AKIA1234567890ABCDEF"\n'
        )

    def queue_and_run(job_id):
        from app.services.scanner.scan_orchestrator import run_scan

        run_scan(job_id)
        return type("QueuedTask", (), {"id": "task-integration"})()

    monkeypatch.setattr(
        "app.services.scanner.repo_cloner.Repo.clone_from", fake_clone
    )
    monkeypatch.setattr(
        "app.services.scanner.scan_orchestrator.review_repository",
        lambda *args: pytest.fail("Gemini must not receive source without opt-in"),
    )
    monkeypatch.setattr(
        "app.api.v1.scan.routes.run_scan_task.delay", queue_and_run
    )
    monkeypatch.setattr("app.api.v1.scan.routes._broker_is_ready", lambda: True)
    client = scan_app.test_client()
    headers = {"Authorization": f"Bearer {token}"}

    started = client.post(
        "/api/v1/scan/start",
        json={"repo_url": "https://github.com/acme/service"},
        headers=headers,
    )
    scan_id = started.get_json()["scan"]["id"]
    result = client.get(f"/api/v1/scan/{scan_id}", headers=headers)

    assert started.status_code == 202
    assert result.status_code == 200
    assert result.get_json()["scan"]["status"] == "completed"
    assert result.get_json()["scan"]["gemini_review_requested"] is False
    assert result.get_json()["result"]["security_score"] is None
    assert result.get_json()["result"]["coverage"]["overall"] == "partial"
    assert result.get_json()["result"]["coverage"]["static_analysis"]["status"] == "partial"
    findings = result.get_json()["findings"]
    assert any(finding["rule_id"] == "CODE001" for finding in findings)
    secret_finding = next(finding for finding in findings if finding["rule_id"] == "SEC001")
    assert secret_finding["matched_text"] != "AKIA1234567890ABCDEF"
    assert "AKIA1234567890ABCDEF" not in result.get_data(as_text=True)


@pytest.mark.parametrize(
    ("repo_url", "branch"),
    [
        ("http://github.com/acme/service", "main"),
        ("https://github.com.evil.example/acme/service", "main"),
        ("https://github.com/acme/service", "-oProxyCommand=evil"),
    ],
)
def test_start_scan_rejects_untrusted_repository_or_branch(scan_app, repo_url, branch):
    token, _ = _create_user_token(scan_app, "scan-invalid", "scan-invalid@example.test")
    response = scan_app.test_client().post(
        "/api/v1/scan/start",
        json={"repo_url": repo_url, "branch": branch},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    with scan_app.app_context():
        assert db.session.query(ScanJob).count() == 0


def test_start_scan_requires_boolean_gemini_consent(scan_app):
    token, _ = _create_user_token(
        scan_app, "scan-consent", "scan-consent@example.test"
    )
    response = scan_app.test_client().post(
        "/api/v1/scan/start",
        json={
            "repo_url": "https://github.com/acme/service",
            "gemini_review": "yes",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400, response.get_json()
    assert response.get_json()["error"] == "gemini_review must be a boolean."


def test_synchronous_audit_includes_gemini_advisories_when_requested(
    scan_app, monkeypatch, tmp_path
):
    token, user_id = _create_user_token(
        scan_app, "scan-sync-gemini", "scan-sync-gemini@example.test"
    )
    review_calls = []

    @contextmanager
    def fake_cloned_repo(repo_url):
        assert repo_url == "https://github.com/acme/service"
        yield str(tmp_path)

    monkeypatch.setattr(
        "app.services.scanner.repo_cloner.cloned_repo", fake_cloned_repo
    )
    monkeypatch.setattr(
        "app.services.scanner.static_analyzer.analyze_repository",
        lambda path: ([], SimpleNamespace(files_scanned=1)),
    )
    monkeypatch.setattr(
        "app.services.scanner.dependency_auditor.audit_dependencies",
        lambda path: SimpleNamespace(findings=[], coverage={}),
    )

    def review_repository(path, requested_user_id):
        review_calls.append((path, requested_user_id))
        return (
            [{
                "rule_id": "AI-GEMINI-01",
                "finding_type": "code_pattern",
                "severity": "medium",
                "title": "Add input validation",
                "description": "Gemini advisory: validate untrusted input.",
                "file_path": "app.py",
                "line_number": 8,
            }],
            "checked",
        )

    monkeypatch.setattr(
        "app.services.scanner.gemini_source_review.review_repository",
        review_repository,
    )

    response = scan_app.test_client().post(
        "/api/audit",
        json={
            "repoUrl": "https://github.com/acme/service",
            "files": [],
            "gemini_review": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["coverage"]["gemini"]["status"] == "checked"
    assert any("Add input validation" in alert["message"] for alert in result["alerts"])
    assert review_calls == [(str(tmp_path), user_id)]


def test_scan_status_and_cancel_are_limited_to_owner(scan_app, monkeypatch):
    owner_token, owner_id = _create_user_token(
        scan_app, "scan-owner-two", "scan-owner-two@example.test"
    )
    other_token, _ = _create_user_token(
        scan_app, "scan-other", "scan-other@example.test"
    )
    with scan_app.app_context():
        job = ScanJob(
            repo_url="https://github.com/acme/service",
            branch="main",
            requested_by=owner_id,
            status=ScanStatusEnum.PENDING,
            celery_task_id="task-cancel",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    client = scan_app.test_client()
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/scan/{job_id}", headers=other_headers).status_code == 404
    assert client.delete(f"/api/v1/scan/{job_id}", headers=other_headers).status_code == 404

    revoked = {}
    monkeypatch.setattr(
        "app.api.v1.scan.routes.celery.control.revoke",
        lambda task_id: revoked.setdefault("task_id", task_id),
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    response = client.delete(f"/api/v1/scan/{job_id}", headers=owner_headers)

    assert response.status_code == 200
    assert revoked["task_id"] == "task-cancel"
    with scan_app.app_context():
        assert db.session.get(ScanJob, job_id).status == ScanStatusEnum.CANCELLED
        from app.services.scanner.scan_orchestrator import run_scan

        monkeypatch.setattr(
            "app.services.scanner.scan_orchestrator.cloned_repo",
            lambda *args, **kwargs: pytest.fail("cancelled scan must not clone"),
        )
        run_scan(job_id)
        assert db.session.get(ScanJob, job_id).status == ScanStatusEnum.CANCELLED


def test_cancel_wins_before_worker_can_claim_pending_scan(scan_app, monkeypatch):
    owner_token, owner_id = _create_user_token(
        scan_app, "scan-race-owner", "scan-race-owner@example.test"
    )
    with scan_app.app_context():
        job = ScanJob(
            repo_url="https://github.com/acme/service",
            branch="main",
            requested_by=owner_id,
            status=ScanStatusEnum.PENDING,
            celery_task_id="task-race",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    worker_claim = {}

    def try_worker_claim(task_id):
        worker_claim["rowcount"] = db.session.execute(
            update(ScanJob)
            .where(
                ScanJob.id == job_id,
                ScanJob.status == ScanStatusEnum.PENDING,
            )
            .values(status=ScanStatusEnum.RUNNING)
        ).rowcount
        db.session.commit()

    monkeypatch.setattr(
        "app.api.v1.scan.routes.celery.control.revoke", try_worker_claim
    )
    response = scan_app.test_client().delete(
        f"/api/v1/scan/{job_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    assert worker_claim["rowcount"] == 0
    with scan_app.app_context():
        assert db.session.get(ScanJob, job_id).status == ScanStatusEnum.CANCELLED


def test_cancel_reports_task_revocation_failure_after_persisting_cancel(
    scan_app, monkeypatch
):
    owner_token, owner_id = _create_user_token(
        scan_app, "scan-revoke-owner", "scan-revoke-owner@example.test"
    )
    with scan_app.app_context():
        job = ScanJob(
            repo_url="https://github.com/acme/service",
            branch="main",
            requested_by=owner_id,
            status=ScanStatusEnum.PENDING,
            celery_task_id="task-revoke-failure",
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    def fail_revoke(task_id):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "app.api.v1.scan.routes.celery.control.revoke", fail_revoke
    )
    response = scan_app.test_client().delete(
        f"/api/v1/scan/{job_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 503
    assert "cancelled" in response.get_json()["error"].lower()
    with scan_app.app_context():
        assert db.session.get(ScanJob, job_id).status == ScanStatusEnum.CANCELLED
