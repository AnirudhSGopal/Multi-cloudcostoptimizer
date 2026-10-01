"""
Application factory.
Keeps the app creation separate from the module-level scope so that
tests can spin up isolated instances.
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config.settings import ProductionConfig, get_config
from app.core.extensions import db, jwt, cors, limiter, migrate, _configure_celery
from sqlalchemy import text


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ── Configuration ─────────────────────────────────────────────────────
    config_class = get_config(config_name)
    if config_class is ProductionConfig:
        config_class.validate()
    app.config.from_object(config_class)
    from app.core.logging_setup import configure_production_logging, init_sentry

    if config_class is ProductionConfig:
        configure_production_logging(app)
        init_sentry(app)

    # ── Extensions ────────────────────────────────────────────────────────
    engine_options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        for option in ("pool_size", "max_overflow", "pool_timeout"):
            engine_options.pop(option, None)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    _configure_celery(app)

    with app.app_context():
        from app.models import user, scan, cloud, cloud_account  # noqa: F401

    # ── CORS Handling (manual) ────────────────────────────────────────────
    # Initialize CORS with Flask-CORS extension
    cors_origins = app.config["CORS_ORIGINS"]
    if "*" in cors_origins:
        raise RuntimeError("CORS_ORIGINS must contain explicit origins, not *")
    cors.init_app(
        app,
        resources={r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": bool(cors_origins),
            "max_age": 3600
        }}
    )

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        if not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # ── Error Handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return jsonify({"error": error.name}), error.code
        app.logger.error("Unhandled exception: %s", type(error).__name__)
        return jsonify({"error": "Internal server error"}), 500

    # ── Blueprints ────────────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Shell context ─────────────────────────────────────────────────────
    @app.shell_context_processor
    def make_shell_context():
        from app.models.user import User
        from app.models.scan import ScanJob, ScanResult, Vulnerability
        from app.models.cloud import CloudMetric
        from app.models.cloud_account import CloudAccount
        return {"db": db, "User": User, "ScanJob": ScanJob,
                "ScanResult": ScanResult, "Vulnerability": Vulnerability,
                "CloudMetric": CloudMetric, "CloudAccount": CloudAccount}

    # ── Health-check ──────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/ready")
    def ready():
        checks = {
            "database": "ok" if _database_is_ready() else "unavailable",
            "redis": "ok" if _redis_is_ready() else "unavailable",
        }
        is_ready = all(status == "ok" for status in checks.values())
        return (
            {"status": "ready" if is_ready else "not_ready", "checks": checks},
            200 if is_ready else 503,
        )

    return app


def _database_is_ready() -> bool:
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        from flask import current_app

        current_app.logger.warning(
            "Readiness database check failed; exception_type=%s",
            type(exc).__name__,
        )
        return False


def _redis_is_ready() -> bool:
    from redis import Redis
    from flask import current_app

    try:
        with Redis.from_url(
            current_app.config["CELERY_BROKER_URL"],
            socket_connect_timeout=2,
            socket_timeout=2,
        ) as redis_client:
            return bool(redis_client.ping())
    except Exception as exc:
        current_app.logger.warning(
            "Readiness Redis check failed; exception_type=%s",
            type(exc).__name__,
        )
        return False


def _register_blueprints(app: Flask):
    from app.api.v1.auth.routes import auth_bp
    from app.api.v1.scan.routes import scan_bp
    from app.api.v1.cloud.routes import cloud_bp
    from app.api.v1.reports.routes import reports_bp
    from app.api.v1.admin.routes import admin_bp
    from app.api.simple_api import simple_api_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/v1/auth")
    app.register_blueprint(scan_bp,      url_prefix="/api/v1/scan")
    app.register_blueprint(cloud_bp,     url_prefix="/api/v1/cloud")
    app.register_blueprint(reports_bp,   url_prefix="/api/v1/reports")
    app.register_blueprint(admin_bp,     url_prefix="/api/v1/admin")
    app.register_blueprint(simple_api_bp, url_prefix="/api")