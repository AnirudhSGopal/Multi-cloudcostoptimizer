"""
Admin API endpoints — platform management for admin users.

All routes are protected by @jwt_required() + @admin_required.
Blueprint prefix: /api/v1/admin

User management:
  GET    /users              – paginated user list
  GET    /users/<id>         – user detail with counts
  PATCH  /users/<id>         – update role or is_active
  DELETE /users/<id>         – delete user (requires ?confirm=true)
  POST   /users/<id>/promote – change user role

Platform oversight:
  GET    /cloud-accounts     – all cloud accounts (no decrypted creds)
  GET    /scans              – all scan jobs
  GET    /stats              – aggregate platform metrics

System health:
  GET    /system-health      – DB, Gemini, Redis, encryption key status
"""
import os
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.core.extensions import db
from app.utils.decorators import admin_required
from app.models.user import User, RoleEnum
from app.models.cloud_account import CloudAccount, AccountStatusEnum
from app.models.cloud import CloudMetric, CloudProviderEnum
from app.models.scan import ScanJob, ScanResult, ScanStatusEnum

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════


@admin_bp.get("/users")
@jwt_required()
@admin_required
def list_users():
    """
    GET /api/v1/admin/users
    Paginated list of all users.
    Query params: page (default 1), per_page (default 20), search (optional)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "", type=str).strip()

    per_page = min(per_page, 100)  # cap

    query = User.query
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users = []
    for u in pagination.items:
        d = u.to_dict()
        d["last_login"] = None  # placeholder — can track later
        users.append(d)

    return jsonify({
        "users": users,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.get("/users/<int:user_id>")
@jwt_required()
@admin_required
def get_user(user_id):
    """
    GET /api/v1/admin/users/<id>
    Single user detail with cloud_accounts_count and scans_count.
    """
    user = User.query.get_or_404(user_id)
    data = user.to_dict()
    data["cloud_accounts_count"] = CloudAccount.query.filter_by(user_id=user.id).count()
    data["scans_count"] = ScanJob.query.filter_by(requested_by=user.id).count()
    return jsonify({"user": data}), 200


@admin_bp.patch("/users/<int:user_id>")
@jwt_required()
@admin_required
def update_user(user_id):
    """
    PATCH /api/v1/admin/users/<id>
    Update role or is_active.
    Body: { "role": "admin"|"analyst"|"viewer", "is_active": true|false }
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "role" in data:
        role_str = str(data["role"]).strip().lower()
        if role_str not in RoleEnum._value2member_map_:
            return jsonify({"error": f"Invalid role. Must be one of {list(RoleEnum._value2member_map_)}"}), 422
        user.role = RoleEnum(role_str)

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"message": "User updated.", "user": user.to_dict()}), 200


@admin_bp.delete("/users/<int:user_id>")
@jwt_required()
@admin_required
def delete_user(user_id):
    """
    DELETE /api/v1/admin/users/<id>?confirm=true
    Delete user and cascade all related data.
    Requires ?confirm=true to prevent accidental calls.
    """
    if request.args.get("confirm", "").lower() != "true":
        return jsonify({"error": "Add ?confirm=true to confirm deletion."}), 400

    user = User.query.get_or_404(user_id)

    # Prevent self-deletion
    from flask_jwt_extended import get_jwt_identity
    current_id = get_jwt_identity()
    if user.id == current_id:
        return jsonify({"error": "Cannot delete your own account."}), 400

    username = user.username
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"User '{username}' and all related data deleted."}), 200


@admin_bp.post("/users/<int:user_id>/promote")
@jwt_required()
@admin_required
def promote_user(user_id):
    """
    POST /api/v1/admin/users/<id>/promote
    Body: { "role": "admin"|"analyst"|"viewer" }
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    role_str = str(data.get("role", "")).strip().lower()

    if role_str not in RoleEnum._value2member_map_:
        return jsonify({"error": f"Invalid role. Must be one of {list(RoleEnum._value2member_map_)}"}), 422

    user.role = RoleEnum(role_str)
    db.session.commit()

    return jsonify({"message": f"User '{user.username}' role changed to {role_str}.", "user": user.to_dict()}), 200


# ═══════════════════════════════════════════════════════════════════════════════
#  PLATFORM OVERSIGHT
# ═══════════════════════════════════════════════════════════════════════════════


@admin_bp.get("/cloud-accounts")
@jwt_required()
@admin_required
def list_all_cloud_accounts():
    """
    GET /api/v1/admin/cloud-accounts
    Every CloudAccount across all users — never exposes decrypted credentials.
    Query params: provider (optional), status (optional), page, per_page
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    provider = request.args.get("provider", "", type=str).strip().lower()
    status = request.args.get("status", "", type=str).strip().lower()

    per_page = min(per_page, 100)

    query = CloudAccount.query
    if provider and provider in CloudProviderEnum._value2member_map_:
        query = query.filter_by(provider=CloudProviderEnum(provider))
    if status and status in AccountStatusEnum._value2member_map_:
        query = query.filter_by(status=AccountStatusEnum(status))

    query = query.order_by(CloudAccount.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    accounts = []
    for acc in pagination.items:
        d = acc.to_dict()
        # Enrich with owner username
        owner = User.query.get(acc.user_id)
        d["username"] = owner.username if owner else "unknown"
        accounts.append(d)

    return jsonify({
        "cloud_accounts": accounts,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.get("/scans")
@jwt_required()
@admin_required
def list_all_scans():
    """
    GET /api/v1/admin/scans
    Every ScanJob across all users.
    Query params: status (optional), page, per_page
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status", "", type=str).strip().lower()

    per_page = min(per_page, 100)

    query = ScanJob.query
    if status and status in ScanStatusEnum._value2member_map_:
        query = query.filter_by(status=ScanStatusEnum(status))

    query = query.order_by(ScanJob.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    scans = []
    for scan in pagination.items:
        d = scan.to_dict()
        # Enrich with owner info and score
        if scan.requested_by:
            owner = User.query.get(scan.requested_by)
            d["username"] = owner.username if owner else "unknown"
        else:
            d["username"] = "unknown"
        if scan.result:
            d["security_score"] = round(scan.result.security_score, 2)
            d["total_findings"] = scan.result.total_findings
        else:
            d["security_score"] = None
            d["total_findings"] = None
        scans.append(d)

    return jsonify({
        "scans": scans,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.get("/stats")
@jwt_required()
@admin_required
def platform_stats():
    """
    GET /api/v1/admin/stats
    Aggregate platform metrics.
    """
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    # Cloud accounts by provider
    accounts_by_provider = {}
    for provider in CloudProviderEnum:
        count = CloudAccount.query.filter_by(provider=provider).count()
        accounts_by_provider[provider.value] = count
    total_cloud_accounts = sum(accounts_by_provider.values())

    # Scans
    total_scans = ScanJob.query.count()
    completed_scans = ScanJob.query.filter_by(status=ScanStatusEnum.COMPLETED).count()
    failed_scans = ScanJob.query.filter_by(status=ScanStatusEnum.FAILED).count()

    # Total recommendations (vulnerabilities found)
    from app.models.scan import Vulnerability
    total_recommendations = Vulnerability.query.count()

    # Total estimated savings (sum of cost_usd across all metrics)
    total_savings_row = db.session.query(func.sum(CloudMetric.cost_usd)).scalar()
    total_estimated_savings = float(total_savings_row) if total_savings_row else 0.0

    # Sync error rate: cloud accounts with status=ERROR / total
    error_accounts = CloudAccount.query.filter_by(status=AccountStatusEnum.ERROR).count()
    sync_error_rate = (error_accounts / total_cloud_accounts * 100) if total_cloud_accounts > 0 else 0.0

    return jsonify({
        "total_users": total_users,
        "active_users": active_users,
        "total_cloud_accounts": total_cloud_accounts,
        "accounts_by_provider": accounts_by_provider,
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "failed_scans": failed_scans,
        "total_recommendations": total_recommendations,
        "total_estimated_savings": round(total_estimated_savings, 2),
        "sync_error_rate": round(sync_error_rate, 2),
    }), 200


# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════════════════════


@admin_bp.get("/system-health")
@jwt_required()
@admin_required
def system_health():
    """
    GET /api/v1/admin/system-health
    Check connectivity to DB, Gemini API, Redis/Celery, and encryption key.
    """
    checks = {}

    # 1. Database connection
    try:
        db.session.execute(db.text("SELECT 1"))
        checks["database"] = {"status": "healthy", "message": "Connection OK"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}

    # 2. Gemini API reachability
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Just list models as a lightweight check
            models = genai.list_models()
            model_count = sum(1 for _ in models)
            checks["gemini_api"] = {"status": "healthy", "message": f"Reachable ({model_count} models available)"}
        else:
            checks["gemini_api"] = {"status": "unhealthy", "message": "GEMINI_API_KEY not set"}
    except Exception as e:
        checks["gemini_api"] = {"status": "unhealthy", "message": str(e)}

    # 3. CLOUD_ENCRYPTION_KEY
    encryption_key = os.getenv("CLOUD_ENCRYPTION_KEY")
    if encryption_key:
        checks["encryption_key"] = {"status": "healthy", "message": "CLOUD_ENCRYPTION_KEY is set"}
    else:
        checks["encryption_key"] = {"status": "unhealthy", "message": "CLOUD_ENCRYPTION_KEY not set"}

    # 4. Redis / Celery
    try:
        from app.core.extensions import celery
        # Attempt a Redis ping via the Celery broker connection
        conn = celery.connection()
        conn.ensure_connection(max_retries=1, timeout=3)
        conn.close()
        checks["celery_redis"] = {"status": "healthy", "message": "Broker connection OK"}
    except Exception as e:
        checks["celery_redis"] = {"status": "unhealthy", "message": f"Broker unreachable: {str(e)}"}

    # Overall status
    all_healthy = all(c["status"] == "healthy" for c in checks.values())

    return jsonify({
        "overall": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }), 200
