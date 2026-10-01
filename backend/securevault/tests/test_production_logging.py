import json
import logging

from app.core.logging_setup import ProductionJsonFormatter


def test_json_logs_redact_emails_tokens_and_credentials():
    record = logging.LogRecord(
        name="securevault.test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg=(
            "login failed for alice@example.test token=secret-token "
            "password=hunter2 key=AKIA1234567890ABCDEF"
        ),
        args=(),
        exc_info=None,
    )

    rendered = ProductionJsonFormatter().format(record)
    event = json.loads(rendered)

    assert event["level"] == "ERROR"
    assert "[REDACTED_EMAIL]" in event["message"]
    assert "secret-token" not in rendered
    assert "hunter2" not in rendered
    assert "AKIA1234567890ABCDEF" not in rendered
