"""
Report generation endpoints — scaffold (501 stubs).

GET  /api/v1/reports/<job_id>/pdf   – download scan report as PDF
GET  /api/v1/reports/<job_id>/json  – download scan report as JSON
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.utils.decorators import active_user_required

reports_bp = Blueprint("reports", __name__)

_NOT_IMPLEMENTED = {"message": "Report generation not yet implemented."}


@reports_bp.get("/<int:job_id>/pdf")
@jwt_required()
@active_user_required
def report_pdf(job_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501


@reports_bp.get("/<int:job_id>/json")
@jwt_required()
@active_user_required
def report_json(job_id: int):
    return jsonify(_NOT_IMPLEMENTED), 501