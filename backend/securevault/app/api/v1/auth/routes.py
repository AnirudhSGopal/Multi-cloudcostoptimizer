"""
Authentication endpoints.

POST  /api/v1/auth/register   – create a new account
POST  /api/v1/auth/login      – obtain access + refresh tokens
POST  /api/v1/auth/refresh    – exchange refresh token for new access token
GET   /api/v1/auth/me         – return current user profile
POST  /api/v1/auth/logout     – client-side: just discard the token
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)

from app.core.extensions import db, limiter
from app.models.user import User, RoleEnum

auth_bp = Blueprint("auth", __name__)


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip().lower()
    password = data.get("password")  or ""
    role_str = (data.get("role") or RoleEnum.VIEWER.value).strip().lower()

    # ── Validation ────────────────────────────────────────────────────────
    errors = {}
    if not username or len(username) < 3:
        errors["username"] = "Must be at least 3 characters."
    if not email or "@" not in email:
        errors["email"] = "Must be a valid email address."
    if len(password) < 8:
        errors["password"] = "Must be at least 8 characters."
    if role_str not in RoleEnum._value2member_map_:
        errors["role"] = f"Must be one of {list(RoleEnum._value2member_map_)}."
    if errors:
        return jsonify({"errors": errors}), 422

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(
        username=username,
        email=email,
        role=RoleEnum(role_str),
    )
    user.password = password
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created.", "user": user.to_dict()}), 201


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.post("/login")
@limiter.limit("20 per hour")
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password   = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "username/email and password are required."}), 400

    user = (
        User.query.filter_by(username=identifier).first()
        or User.query.filter_by(email=identifier.lower()).first()
    )

    if user is None or not user.verify_password(password):
        return jsonify({"error": "Invalid credentials."}), 401
    if not user.is_active:
        return jsonify({"error": "Account is disabled."}), 403

    access_token  = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          user.to_dict(),
    }), 200


# ── Refresh ───────────────────────────────────────────────────────────────────

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None or not user.is_active:
        return jsonify({"error": "User not found or inactive."}), 401

    new_access = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access}), 200


# ── Me ────────────────────────────────────────────────────────────────────────

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user.to_dict()}), 200


# ── Logout (client-side token discard) ────────────────────────────────────────

@auth_bp.post("/logout")
@jwt_required()
def logout():
    # Stateless JWT — instruct the client to discard the token.
    # For server-side revocation, integrate a token blocklist (Redis) here.
    return jsonify({"message": "Logged out. Discard your tokens on the client."}), 200