"""
Application factory.
Keeps the app creation separate from the module-level scope so that
tests can spin up isolated instances.
"""
from flask import Flask

from config.settings import get_config
from app.core.extensions import db, jwt, cors, limiter, _configure_celery


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ── Configuration ─────────────────────────────────────────────────────
    app.config.from_object(get_config(config_name))

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)
    _configure_celery(app)

    # ── Blueprints ────────────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Shell context ─────────────────────────────────────────────────────
    @app.shell_context_processor
    def make_shell_context():
        from app.models.user import User
        from app.models.scan import ScanJob, ScanResult, Vulnerability
        from app.models.cloud import CloudMetric
        return {"db": db, "User": User, "ScanJob": ScanJob,
                "ScanResult": ScanResult, "Vulnerability": Vulnerability,
                "CloudMetric": CloudMetric}

    # ── Health-check ──────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    return app


def _register_blueprints(app: Flask):
    from app.api.v1.auth.routes import auth_bp
    from app.api.v1.scan.routes import scan_bp
    from app.api.v1.cloud.routes import cloud_bp
    from app.api.v1.reports.routes import reports_bp

    app.register_blueprint(auth_bp,    url_prefix="/api/v1/auth")
    app.register_blueprint(scan_bp,    url_prefix="/api/v1/scan")
    app.register_blueprint(cloud_bp,   url_prefix="/api/v1/cloud")
    app.register_blueprint(reports_bp, url_prefix="/api/v1/reports")