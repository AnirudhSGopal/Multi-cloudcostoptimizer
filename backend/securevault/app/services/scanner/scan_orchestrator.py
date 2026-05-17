"""
Scan orchestrator.
Coordinates the full scan pipeline:
  1. Clone repository
  2. Run static analysis
  3. Run dependency audit
  4. Calculate security score
  5. Persist all findings to PostgreSQL
"""
import logging
import time
from datetime import datetime, timezone

from app.core.extensions import db
from app.models.scan import (
    ScanJob, ScanResult, Vulnerability,
    ScanStatusEnum, SeverityEnum,
)
from app.services.scanner.repo_cloner import cloned_repo, CloneError
from app.services.scanner.static_analyzer import analyze_repository
from app.services.scanner.dependency_auditor import audit_dependencies

logger = logging.getLogger(__name__)


# ── Scoring constants ─────────────────────────────────────────────────────────
# Score starts at 100 and is reduced by the weight of each finding.
# Maximum deduction per severity bucket is capped to keep the scale fair.

SEVERITY_DEDUCTIONS: dict[SeverityEnum, float] = {
    SeverityEnum.CRITICAL: 20.0,
    SeverityEnum.HIGH:     10.0,
    SeverityEnum.MEDIUM:    5.0,
    SeverityEnum.LOW:       2.0,
    SeverityEnum.INFO:      0.0,
}

MAX_DEDUCTION_PER_BUCKET: dict[SeverityEnum, float] = {
    SeverityEnum.CRITICAL: 60.0,
    SeverityEnum.HIGH:     30.0,
    SeverityEnum.MEDIUM:   20.0,
    SeverityEnum.LOW:       5.0,
    SeverityEnum.INFO:      0.0,
}


# ── Public API ────────────────────────────────────────────────────────────────

def run_scan(job_id: int) -> None:
    """
    Execute the full scan pipeline for *job_id*.
    Updates ScanJob.status throughout and writes ScanResult + Vulnerability rows.
    All exceptions are caught; job.status is set to FAILED on any error.
    """
    job: ScanJob | None = ScanJob.query.get(job_id)
    if job is None:
        logger.error("ScanJob %d not found — aborting.", job_id)
        return

    _update_status(job, ScanStatusEnum.RUNNING)
    start_time = time.monotonic()

    try:
        with cloned_repo(job.repo_url, job.branch) as repo_path:
            logger.info("[Job %d] Cloned to %s", job_id, repo_path)

            # ── Phase 1: Static analysis ──────────────────────────────────
            static_findings, stats = analyze_repository(repo_path)
            logger.info("[Job %d] Static: %d findings in %d files",
                        job_id, len(static_findings), stats.files_scanned)

            # ── Phase 2: Dependency audit ─────────────────────────────────
            dep_findings = audit_dependencies(repo_path)
            logger.info("[Job %d] Dependencies: %d findings", job_id, len(dep_findings))

            all_findings = static_findings + dep_findings

        # ── Phase 3: Persist ──────────────────────────────────────────────
        duration = time.monotonic() - start_time
        _persist_results(job, all_findings, stats, duration)
        _update_status(job, ScanStatusEnum.COMPLETED)
        logger.info("[Job %d] Completed in %.1f s with %d findings.",
                    job_id, duration, len(all_findings))

    except CloneError as exc:
        _fail(job, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("[Job %d] Unexpected error: %s", job_id, exc)
        _fail(job, f"Internal error: {exc}")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _persist_results(
    job: ScanJob,
    findings: list[dict],
    stats,
    duration: float,
) -> None:
    """Write Vulnerability rows and a ScanResult summary."""
    severity_counts: dict[SeverityEnum, int] = {s: 0 for s in SeverityEnum}

    for f in findings:
        vuln = Vulnerability(
            job_id        = job.id,
            finding_type  = f["finding_type"],
            severity      = f["severity"],
            rule_id       = f["rule_id"],
            title         = f["title"],
            description   = f.get("description"),
            file_path     = f.get("file_path"),
            line_number   = f.get("line_number"),
            matched_text  = f.get("matched_text"),
            cve_id        = f.get("cve_id"),
            package_name  = f.get("package_name"),
            package_version = f.get("package_version"),
            fix_version   = f.get("fix_version"),
            remediation   = f.get("remediation"),
        )
        db.session.add(vuln)
        severity_counts[f["severity"]] += 1

    score = _calculate_score(severity_counts)

    result = ScanResult(
        job_id          = job.id,
        security_score  = score,
        total_findings  = len(findings),
        critical_count  = severity_counts[SeverityEnum.CRITICAL],
        high_count      = severity_counts[SeverityEnum.HIGH],
        medium_count    = severity_counts[SeverityEnum.MEDIUM],
        low_count       = severity_counts[SeverityEnum.LOW],
        info_count      = severity_counts[SeverityEnum.INFO],
        files_scanned   = stats.files_scanned,
        lines_scanned   = stats.lines_scanned,
        scan_duration_s = round(duration, 2),
    )
    db.session.add(result)
    db.session.commit()


def _calculate_score(counts: dict[SeverityEnum, int]) -> float:
    """Compute 0–100 security score from finding counts."""
    deduction = 0.0
    for severity, count in counts.items():
        per_finding = SEVERITY_DEDUCTIONS[severity]
        max_ded     = MAX_DEDUCTION_PER_BUCKET[severity]
        deduction  += min(count * per_finding, max_ded)
    return max(0.0, 100.0 - deduction)


def _update_status(job: ScanJob, status: ScanStatusEnum) -> None:
    job.status = status
    if status == ScanStatusEnum.RUNNING:
        job.started_at = datetime.now(timezone.utc)
    elif status in (ScanStatusEnum.COMPLETED, ScanStatusEnum.FAILED):
        job.finished_at = datetime.now(timezone.utc)
    db.session.commit()


def _fail(job: ScanJob, message: str) -> None:
    job.error_msg = message
    _update_status(job, ScanStatusEnum.FAILED)
    logger.error("[Job %d] FAILED: %s", job.id, message)