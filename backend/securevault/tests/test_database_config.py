import pytest

from app.core.extensions import db
from app.core.factory import create_app
from config.settings import BaseConfig, _normalize_database_url


def test_database_url_normalizes_postgres_scheme_and_requires_remote_tls():
    url = _normalize_database_url(
        "postgres://app:example-password@db.example.test:5432/securevault"
    )

    assert url.startswith("postgresql://")
    assert "sslmode=require" in url


def test_database_url_preserves_local_postgres_without_forcing_tls():
    url = _normalize_database_url(
        "postgres://app:example-password@localhost:5432/securevault"
    )

    assert url.startswith("postgresql://")
    assert "sslmode" not in url


def test_database_url_replaces_weak_remote_sslmode():
    url = _normalize_database_url(
        "postgresql://app:example-password@db.example.test/securevault?sslmode=disable"
    )

    assert "sslmode=require" in url
    assert "sslmode=disable" not in url


def test_factory_does_not_create_tables_implicitly(monkeypatch):
    def unexpected_create_all():
        raise AssertionError("The app factory must not create tables")

    monkeypatch.setattr(db, "create_all", unexpected_create_all)
    create_app("testing")


def test_common_foreign_key_filters_have_indexes():
    from app.models.cloud import CloudMetric
    from app.models.scan import ScanJob

    assert CloudMetric.cloud_account_id.index is True
    assert CloudMetric.collected_at.index is True
    assert ScanJob.requested_by.index is True


def test_database_pool_defaults_are_bounded_for_small_poolers():
    options = BaseConfig.SQLALCHEMY_ENGINE_OPTIONS

    assert options["pool_pre_ping"] is True
    assert options["pool_recycle"] == 300
    assert options["pool_size"] == 2
    assert options["max_overflow"] == 1
    assert options["pool_timeout"] == 30


def test_rate_limits_use_configured_redis_storage():
    assert BaseConfig.RATELIMIT_STORAGE_URI.startswith("redis://")


@pytest.mark.parametrize("url", ["sqlite:///:memory:", None])
def test_database_url_handles_sqlite_and_missing_values(url):
    assert _normalize_database_url(url) == url
