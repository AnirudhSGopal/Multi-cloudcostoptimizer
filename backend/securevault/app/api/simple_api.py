"""
Simple REST API for frontend integration.
Handles basic security audit and authentication.
"""
import logging
from pathlib import PurePosixPath, PureWindowsPath
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.core.extensions import limiter
from app.utils.decorators import active_user_required

simple_api_bp = Blueprint("simple_api", __name__)
logger = logging.getLogger(__name__)




# ── Audit Helper ──────────────────────────────────────────────────────────────

def _map_rule_based_finding(f, index):
    sev = f.get("severity")
    if hasattr(sev, "value"):
        sev = sev.value
    sev = str(sev).lower()

    if sev in ("critical", "high"):
        severity = "critical"
    elif sev in ("medium", "low"):
        severity = "warning"
    else:
        severity = "info"

    loc = f.get("file_path") or "Unknown"
    if f.get("line_number"):
        loc = f"{loc}:{f['line_number']}"

    title = f.get("title") or "Vulnerability"
    desc = f.get("description") or ""
    matched = f.get("matched_text") or ""
    
    msg = title
    if desc:
        msg = f"{msg}: {desc}"
    if matched:
        msg = f"{msg} (Matched: {matched})"

    return {
        "id": f"rb-{f.get('rule_id', 'unknown')}-{index}",
        "severity": severity,
        "message": msg,
        "location": loc
    }


# ── Audit ─────────────────────────────────────────────────────────────────────

@simple_api_bp.post("/audit")
@jwt_required()
@limiter.limit("5 per hour")
@active_user_required
def audit():
    """
    POST /api/audit (protected)
    { repoUrl, files: [{ name, content }] } -> { overall, alerts, compliance }
    """
    data = request.get_json(silent=True) or {}
    repo_url = data.get("repoUrl")
    files = data.get("files", [])
    gemini_review = data.get("gemini_review", False)

    if not repo_url and not files:
        return jsonify({"detail": "repoUrl or files required"}), 400
    if not isinstance(gemini_review, bool):
        return jsonify({"detail": "gemini_review must be a boolean"}), 400
    if gemini_review and not repo_url:
        return jsonify({"detail": "gemini_review requires a repository URL"}), 400
    if not isinstance(files, list):
        return jsonify({"detail": "files must be a list"}), 400
    for uploaded_file in files:
        if not isinstance(uploaded_file, dict):
            return jsonify({"detail": "Each file must include a name and content"}), 400
        name = uploaded_file.get("name")
        if not isinstance(name, str) or not name.strip():
            return jsonify({"detail": "Each file must include a valid name"}), 400
        normalized_name = name.replace("\\", "/")
        relative_path = PurePosixPath(normalized_name)
        if (
            relative_path.is_absolute()
            or PureWindowsPath(name).is_absolute()
            or PureWindowsPath(name).drive
            or ".." in relative_path.parts
        ):
            return jsonify({"detail": "File names must stay within the audit workspace"}), 400
        if not isinstance(uploaded_file.get("content", ""), str):
            return jsonify({"detail": "File content must be text"}), 400

    dependency_coverage = {
        "python": "not_present",
        "npm": "not_present",
        "maven": "not_present",
        "gradle": "not_present",
    }
    rule_based_findings = []
    stats = None
    gemini_status = "not_requested"

    if repo_url:
        from app.services.scanner.repo_cloner import cloned_repo, CloneError
        from app.services.scanner.static_analyzer import analyze_repository
        from app.services.scanner.dependency_auditor import audit_dependencies
        from app.services.scanner.gemini_source_review import review_repository
        try:
            with cloned_repo(repo_url) as clone_dir:
                # ── Run Rule-Based Scanner ──
                try:
                    static_findings, stats = analyze_repository(clone_dir)
                    rule_based_findings.extend(static_findings)
                except Exception as exc:
                    logger.error(
                        "Repository static analysis failed; exception_type=%s",
                        type(exc).__name__,
                    )
                    return jsonify({"detail": "Repository analysis failed"}), 500

                # ── Run Dependency Auditor ──
                try:
                    dependency_report = audit_dependencies(clone_dir)
                    rule_based_findings.extend(dependency_report.findings)
                    dependency_coverage = dependency_report.coverage
                except Exception as exc:
                    logger.error(
                        "Repository dependency audit failed; exception_type=%s",
                        type(exc).__name__,
                    )
                    return jsonify({"detail": "Dependency analysis failed"}), 500

                if gemini_review:
                    advisory_findings, gemini_status = review_repository(
                        clone_dir,
                        int(get_jwt_identity()),
                    )
                    rule_based_findings.extend(advisory_findings)

        except CloneError as e:
            logger.warning("Repository fetch rejected; reason=%s", type(e).__name__)
            return jsonify({"detail": "Repository could not be fetched"}), 400
        except Exception as exc:
            logger.error(
                "Repository audit failed; exception_type=%s",
                type(exc).__name__,
            )
            return jsonify({"detail": "Repository audit failed"}), 500

    if files:
        from app.services.scanner.static_analyzer import analyze_repository
        from app.services.scanner.dependency_auditor import audit_dependencies
        import tempfile
        from pathlib import Path

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                for uploaded_file in files:
                    fpath = (
                        Path(temp_dir) / uploaded_file["name"].replace("\\", "/")
                    ).resolve()
                    if not fpath.is_relative_to(Path(temp_dir).resolve()):
                        return jsonify({
                            "detail": "File names must stay within the audit workspace"
                        }), 400
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    fpath.write_text(uploaded_file.get("content", ""), encoding="utf-8")

                static_findings, stats = analyze_repository(temp_dir)
                rule_based_findings.extend(static_findings)
                dependency_report = audit_dependencies(temp_dir)
                rule_based_findings.extend(dependency_report.findings)
                dependency_coverage = dependency_report.coverage
        except Exception as exc:
            logger.error(
                "Uploaded file audit failed; exception_type=%s",
                type(exc).__name__,
            )
            return jsonify({"detail": "Uploaded file audit failed"}), 500

    # Map and merge rule-based findings
    merged_alerts = []
    seen_keys = set()

    for idx, f in enumerate(rule_based_findings):
        a = _map_rule_based_finding(f, idx)
        key = (str(a.get("severity")).lower(), str(a.get("message")).lower(), str(a.get("location")).lower())
        if key not in seen_keys:
            seen_keys.add(key)
            merged_alerts.append(a)

    return jsonify({
        "alerts": merged_alerts[:15],
        "compliance": [],
        "analysis_status": "partial",
        "files_scanned": stats.files_scanned if stats is not None else 0,
        "coverage": {
            "overall": "partial",
            "static_analysis": {
                "status": "partial",
                "note": "Rule-based checks do not establish that a repository is secure.",
            },
            "dependencies": dependency_coverage,
            "gemini": {
                "status": gemini_status,
                "type": "advisory review",
            },
        },
        "warning": (
            "Results include enabled rule-based checks only; "
            "no overall security score is available."
        ),
    }), 200
