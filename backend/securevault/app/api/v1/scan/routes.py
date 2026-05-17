"""
Scan endpoints — security scanning orchestration.

POST   /api/v1/scan/start       – initiate a repository scan
GET    /api/v1/scan/<job_id>    – get scan status and results
DELETE /api/v1/scan/<job_id>    – cancel an in-progress scan
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.utils.decorators import active_user_required

scan_bp = Blueprint("scan", __name__)

_NOT_IMPLEMENTED = {"message": "Scan endpoints not yet implemented."}


@scan_bp.post("/start")
@jwt_required()
@active_user_required
def start_scan():
    return jsonify(_NOT_IMPLEMENTED), 501


@scan_bp.get("/<int:job_id>")
@jwt_required()
@active_user_required
def get_scan_status(job_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501


@scan_bp.delete("/<int:job_id>")
@jwt_required()
@active_user_required
def cancel_scan(job_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501