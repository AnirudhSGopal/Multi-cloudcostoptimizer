import json

from flask import Flask

from app.services.scanner import gemini_source_review as review


def test_gemini_review_sends_only_bounded_redacted_source(monkeypatch, tmp_path):
    (tmp_path / "service.py").write_text(
        'def run():\n    eval(user_input)\n'
        'api_key = "AIza1234567890abcdefghijklmnopqrstuv"\n'
        'owner = "person@example.test"\n',
        encoding="utf-8",
    )
    app = Flask(__name__)
    app.config.update(
        GEMINI_API_KEY="test-api-key",
        GEMINI_REQUEST_TIMEOUT_SECONDS=2,
    )
    observed = {}
    successes = []
    monkeypatch.setattr(review.gemini_guard, "gemini_circuit_is_open", lambda: False)
    monkeypatch.setattr(review.gemini_guard, "reserve_gemini_call", lambda user_id: True)
    monkeypatch.setattr(review.gemini_guard, "record_gemini_success", lambda: successes.append(True))
    monkeypatch.setattr(review.gemini_guard, "record_gemini_failure", lambda: None)

    def fake_generate(api_key, prompt):
        observed["key"] = api_key
        observed["prompt"] = prompt
        return json.dumps({
            "findings": [{
                "severity": "high",
                "title": "Unsafe dynamic execution",
                "description": "Untrusted input reaches eval.",
                "file_path": "service.py",
                "line_number": 2,
                "remediation": "Remove dynamic execution.",
                "confidence": 0.92,
            }]
        })

    monkeypatch.setattr(review, "_generate_review", fake_generate)

    with app.app_context():
        findings, status = review.review_repository(str(tmp_path), 7)

    assert status == "checked"
    assert observed["key"] == "test-api-key"
    assert "AIza1234567890abcdefghijklmnopqrstuv" not in observed["prompt"]
    assert "person@example.test" not in observed["prompt"]
    assert "eval(user_input)" in observed["prompt"]
    assert findings[0]["rule_id"] == "AI-GEMINI-01"
    assert findings[0]["file_path"] == "service.py"
    assert findings[0]["line_number"] == 2
    assert "advisory" in findings[0]["description"].lower()
    assert successes == [True]


def test_gemini_review_requires_configuration_and_fails_closed(monkeypatch, tmp_path):
    app = Flask(__name__)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        review.gemini_guard,
        "gemini_circuit_is_open",
        lambda: (_ for _ in ()).throw(AssertionError("must not check the provider")),
    )

    with app.app_context():
        findings, status = review.review_repository(str(tmp_path), 7)

    assert findings == []
    assert status == "not_configured"


def test_gemini_review_rejects_untrusted_model_findings(monkeypatch, tmp_path):
    (tmp_path / "safe.py").write_text("value = 1\n", encoding="utf-8")
    app = Flask(__name__)
    app.config["GEMINI_API_KEY"] = "test-api-key"
    failures = []
    monkeypatch.setattr(review.gemini_guard, "gemini_circuit_is_open", lambda: False)
    monkeypatch.setattr(review.gemini_guard, "reserve_gemini_call", lambda user_id: True)
    monkeypatch.setattr(review.gemini_guard, "record_gemini_failure", lambda: failures.append(True))
    monkeypatch.setattr(
        review,
        "_generate_review",
        lambda api_key, prompt: '{"findings": "not-an-array"}',
    )

    with app.app_context():
        findings, status = review.review_repository(str(tmp_path), 7)

    assert findings == []
    assert status == "unavailable"
    assert failures == [True]
