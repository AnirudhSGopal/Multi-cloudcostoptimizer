"""
Cloud provider integration endpoints — Objective 1.

GET    /api/v1/cloud/          – list connected cloud accounts
POST   /api/v1/cloud/          – add new cloud account
GET    /api/v1/cloud/<id>      – get cloud account details
DELETE /api/v1/cloud/<id>      – remove cloud account
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.utils.decorators import active_user_required

cloud_bp = Blueprint("cloud", __name__)

_NOT_IMPLEMENTED = {"message": "Cloud integration endpoints not yet implemented."}


@cloud_bp.get("/")
@jwt_required()
@active_user_required
def list_cloud_accounts():
    return jsonify(_NOT_IMPLEMENTED), 501


@cloud_bp.post("/")
@jwt_required()
@active_user_required
def add_cloud_account():
    return jsonify(_NOT_IMPLEMENTED), 501


@cloud_bp.get("/<int:account_id>")
@jwt_required()
@active_user_required
def get_cloud_account(account_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501


@cloud_bp.delete("/<int:account_id>")
@jwt_required()
@active_user_required
def delete_cloud_account(account_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501

def _get_job_or_404(job_id: int) -> ScanJob:
    from flask import abort
    from flask_jwt_extended import get_jwt_identity
    from app.models.user import User

    job = ScanJob.query.get_or_404(job_id)
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user.is_admin() and job.requested_by != user_id:
        abort(403)
    return job