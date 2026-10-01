from botocore.config import Config

from app.services.cloud import aws


def test_aws_provider_config_uses_bounded_network_timeouts(monkeypatch):
    captured = {}

    class FakeClient:
        def get_caller_identity(self):
            return {"Account": "123", "Arn": "arn:example", "UserId": "user"}

    class FakeSession:
        def __init__(self, **kwargs):
            pass

        def client(self, service_name, **kwargs):
            captured[service_name] = kwargs.get("config")
            return FakeClient()

    monkeypatch.setattr(aws.boto3, "Session", FakeSession)
    result = aws.validate_credentials("test-access", "test-secret")

    assert result["success"] is True
    assert isinstance(captured["sts"], Config)
    assert captured["sts"].connect_timeout <= 10
    assert captured["sts"].read_timeout <= 30
