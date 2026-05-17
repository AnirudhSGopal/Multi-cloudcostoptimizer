"""
Application configuration — Dev / Test / Prod.
All secrets are read from environment variables; sane defaults only for dev.
"""
import os
from datetime import timedelta


class BaseConfig:
    # ── Core ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql://securevault:securevault@localhost:5432/securevault_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)

    # ── Celery / Redis ────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_ACKS_LATE: bool = True

    # ── Rate limiting ─────────────────────────────────────────────────────
    RATELIMIT_STORAGE_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    RATELIMIT_DEFAULT: str = "200 per day;50 per hour"

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # ── Scanner ───────────────────────────────────────────────────────────
    CLONE_BASE_DIR: str = os.getenv("CLONE_BASE_DIR", "/tmp/securevault_repos")
    MAX_REPO_SIZE_MB: int = int(os.getenv("MAX_REPO_SIZE_MB", "500"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://securevault:securevault@localhost:5432/securevault_test",
    )
    CELERY_TASK_ALWAYS_EAGER = True   # run tasks synchronously in tests
    CELERY_TASK_EAGER_PROPAGATES = True
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    # In production every secret MUST come from the environment.
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI: str = os.environ["DATABASE_URL"]


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str = "development"):
    return config_map.get(name, DevelopmentConfig)