"""
Custom decorators for role-based access control.

Usage:
    @jwt_required()
    @roles_required(RoleEnum.ADMIN)
    def admin_only_view(): ...

    @jwt_required()
    @analyst_or_above
    def analyst_view(): ...
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.models.user import User, RoleEnum


def roles_required(*roles: RoleEnum):
    """Allow only users whose role is in *roles*."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _get_current_user()
            if user is None:
                return jsonify({"error": "User not found"}), 404
            if not user.has_role(*roles):
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def analyst_or_above(fn):
    """Allow admin and analyst roles."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if user is None:
            return jsonify({"error": "User not found"}), 404
        if not user.is_analyst_or_above():
            return jsonify({"error": "Analyst or above required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def active_user_required(fn):
    """Reject deactivated accounts."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if user is None:
            return jsonify({"error": "User not found"}), 404
        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_current_user() -> User | None:
    """Return the User object from the JWT identity claim."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)