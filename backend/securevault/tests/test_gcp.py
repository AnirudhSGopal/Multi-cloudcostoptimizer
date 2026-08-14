import pytest
from unittest.mock import MagicMock, patch
from app.services.cloud.gcp import validate_credentials

DUMMY_SA_JSON = """{
  "type": "service_account",
  "project_id": "cloudopt-test",
  "private_key_id": "12345",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "cloudopt-integration@cloudopt-test.iam.gserviceaccount.com",
  "client_id": "100000000000000000000"
}"""

def test_validate_credentials_invalid_json():
    res = validate_credentials("invalid json", "cloudopt-test")
    assert res["success"] is False
    assert "Invalid GCP Service Account JSON format" in res["error"]

def test_validate_credentials_invalid_type():
    res = validate_credentials('{"type": "user"}', "cloudopt-test")
    assert res["success"] is False
    assert "must be a service_account" in res["error"]

@patch("google.oauth2.service_account.Credentials.from_service_account_info")
@patch("google.cloud.storage.Client")
def test_validate_credentials_permission_denied(mock_storage_client, mock_creds):
    mock_creds_instance = MagicMock()
    mock_creds.return_value = mock_creds_instance
    mock_storage_instance = MagicMock()
    mock_storage_client.return_value = mock_storage_instance
    mock_storage_instance.list_buckets.side_effect = Exception(
        "403 GET https://storage.googleapis.com/storage/v1/b?maxResults=1: "
        "cloudopt-integration@cloudopt-test.iam.gserviceaccount.com does not have storage.buckets.list access"
    )

    with patch("google.auth.transport.requests.Request"):
        res = validate_credentials(DUMMY_SA_JSON, "cloudopt-test")

    assert res["success"] is True
    assert res["data"]["warnings"] is not None
    assert "Missing 'storage.buckets.list' permission" in res["data"]["warnings"][0]


@patch("google.oauth2.service_account.Credentials.from_service_account_info")
@patch("google.cloud.storage.Client")
def test_validate_credentials_success(mock_storage_client, mock_creds):
    mock_creds_instance = MagicMock()
    mock_creds.return_value = mock_creds_instance
    mock_storage_instance = MagicMock()
    mock_storage_client.return_value = mock_storage_instance
    mock_storage_instance.list_buckets.return_value = []

    with patch("google.auth.transport.requests.Request"):
        res = validate_credentials(DUMMY_SA_JSON, "cloudopt-test")

    assert res["success"] is True
    assert res["data"]["project_id"] == "cloudopt-test"
    assert res["data"]["client_email"] == "cloudopt-integration@cloudopt-test.iam.gserviceaccount.com"
