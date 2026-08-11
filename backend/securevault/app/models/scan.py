"""
Scan-related models.

ScanJob        – one scan request (one repo URL → one job)
ScanResult     – aggregated summary written when the job finishes
Vulnerability  – individual finding produced by the scanner
"""
import enum
from datetime import datetime, timezone

from app.core.extensions import db


# ── Enumerations ──────────────────────────────────────────────────────────────

class ScanStatusEnum(str, enum.Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


class SeverityEnum(str, enum.Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class FindingTypeEnum(str, enum.Enum):
    SECRET           = "secret"
    CODE_PATTERN     = "code_pattern"
    DEPENDENCY       = "dependency"
    MISCONFIGURATION = "misconfiguration"


# ── Models ────────────────────────────────────────────────────────────────────

class ScanJob(db.Model):
    __tablename__ = "scan_jobs"

    id           = db.Column(db.Integer, primary_key=True)
    celery_task_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    repo_url     = db.Column(db.String(512), nullable=False)
    branch       = db.Column(db.String(128), nullable=False, default="main")
    status       = db.Column(db.Enum(ScanStatusEnum),
                             nullable=False, default=ScanStatusEnum.PENDING, index=True)
    error_msg    = db.Column(db.Text, nullable=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=True)
    created_at   = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc))
    started_at   = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_at  = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    owner          = db.relationship("User", back_populates="scan_jobs")
    result         = db.relationship("ScanResult", back_populates="job",
                                     uselist=False, cascade="all, delete-orphan")
    vulnerabilities = db.relationship("Vulnerability", back_populates="job",
                                      lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "celery_task_id": self.celery_task_id,
            "repo_url":      self.repo_url,
            "branch":        self.branch,
            "status":        self.status.value,
            "error_msg":     self.error_msg,
            "requested_by":  self.requested_by,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
            "started_at":    self.started_at.isoformat() if self.started_at else None,
            "finished_at":   self.finished_at.isoformat() if self.finished_at else None,
        }

    def __repr__(self):
        return f"<ScanJob id={self.id} status={self.status.value}>"


class ScanResult(db.Model):
    __tablename__ = "scan_results"

    id              = db.Column(db.Integer, primary_key=True)
    job_id          = db.Column(db.Integer, db.ForeignKey("scan_jobs.id", ondelete="CASCADE"),
                                unique=True, nullable=False)
    security_score  = db.Column(db.Float, nullable=False, default=100.0)   # 0–100
    total_findings  = db.Column(db.Integer, nullable=False, default=0)
    critical_count  = db.Column(db.Integer, nullable=False, default=0)
    high_count      = db.Column(db.Integer, nullable=False, default=0)
    medium_count    = db.Column(db.Integer, nullable=False, default=0)
    low_count       = db.Column(db.Integer, nullable=False, default=0)
    info_count      = db.Column(db.Integer, nullable=False, default=0)
    files_scanned   = db.Column(db.Integer, nullable=False, default=0)
    lines_scanned   = db.Column(db.Integer, nullable=False, default=0)
    scan_duration_s = db.Column(db.Float, nullable=True)
    created_at      = db.Column(db.DateTime(timezone=True),
                                default=lambda: datetime.now(timezone.utc))

    job = db.relationship("ScanJob", back_populates="result")

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "job_id":          self.job_id,
            "security_score":  round(self.security_score, 2),
            "total_findings":  self.total_findings,
            "critical_count":  self.critical_count,
            "high_count":      self.high_count,
            "medium_count":    self.medium_count,
            "low_count":       self.low_count,
            "info_count":      self.info_count,
            "files_scanned":   self.files_scanned,
            "lines_scanned":   self.lines_scanned,
            "scan_duration_s": self.scan_duration_s,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ScanResult job={self.job_id} score={self.security_score}>"


class Vulnerability(db.Model):
    __tablename__ = "vulnerabilities"

    id           = db.Column(db.Integer, primary_key=True)
    job_id       = db.Column(db.Integer, db.ForeignKey("scan_jobs.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    finding_type = db.Column(db.Enum(FindingTypeEnum), nullable=False)
    severity     = db.Column(db.Enum(SeverityEnum), nullable=False, index=True)
    rule_id      = db.Column(db.String(64),  nullable=False)
    title        = db.Column(db.String(256), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    file_path    = db.Column(db.String(512), nullable=True)
    line_number  = db.Column(db.Integer,     nullable=True)
    matched_text = db.Column(db.Text,        nullable=True)   # redacted snippet
    cve_id       = db.Column(db.String(32),  nullable=True)   # for dependency findings
    package_name = db.Column(db.String(128), nullable=True)
    package_version = db.Column(db.String(64), nullable=True)
    fix_version  = db.Column(db.String(64),  nullable=True)
    remediation  = db.Column(db.Text,        nullable=True)
    created_at   = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc))

    job = db.relationship("ScanJob", back_populates="vulnerabilities")

    # severity → numeric weight used by the scoring engine
    SEVERITY_WEIGHTS: dict = {
        SeverityEnum.CRITICAL: 25,
        SeverityEnum.HIGH:     15,
        SeverityEnum.MEDIUM:    7,
        SeverityEnum.LOW:       3,
        SeverityEnum.INFO:      0,
    }

    def weight(self) -> int:
        return self.SEVERITY_WEIGHTS.get(self.severity, 0)

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "job_id":          self.job_id,
            "finding_type":    self.finding_type.value,
            "severity":        self.severity.value,
            "rule_id":         self.rule_id,
            "title":           self.title,
            "description":     self.description,
            "file_path":       self.file_path,
            "line_number":     self.line_number,
            "matched_text":    self.matched_text,
            "cve_id":          self.cve_id,
            "package_name":    self.package_name,
            "package_version": self.package_version,
            "fix_version":     self.fix_version,
            "remediation":     self.remediation,
        }

    def __repr__(self):
        return f"<Vulnerability {self.rule_id} {self.severity.value} @ {self.file_path}:{self.line_number}>"