"""
Application factory.
Keeps the app creation separate from the module-level scope so that
tests can spin up isolated instances.
"""
from flask import Flask, request, jsonify

from config.settings import get_config
from app.core.extensions import db, jwt, cors, limiter, _configure_celery


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ── Configuration ─────────────────────────────────────────────────────
    app.config.from_object(get_config(config_name))

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    _configure_celery(app)

    # ── CORS Handling (manual) ────────────────────────────────────────────
    # Initialize CORS with Flask-CORS extension
    cors.init_app(
        app,
        resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "max_age": 3600
        }}
    )

    # ── Error Handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Method not allowed"}), 405

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

    return app


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