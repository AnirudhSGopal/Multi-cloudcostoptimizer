"""
Static analyser — walks a repository directory tree and applies
regex rules from secrets.py and code_patterns.py to every source file.

Returns a list of raw finding dicts that scan_orchestrator.py persists.
"""
import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from app.services.scanner.rules.secrets import SECRET_RULES
from app.services.scanner.rules.code_patterns import CODE_RULES

logger = logging.getLogger(__name__)

# ── File-type filters ─────────────────────────────────────────────────────────

SCANNABLE_EXTENSIONS: set[str] = {
    # Python
    ".py", ".pyw",
    # JavaScript / TypeScript
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    # Config / infra
    ".env", ".cfg", ".ini", ".toml", ".yaml", ".yml", ".json",
    ".tf", ".tfvars", ".hcl",
    # Web
    ".html", ".htm", ".jinja", ".jinja2",
    # Shell
    ".sh", ".bash", ".zsh",
    # Ruby / PHP / Go / Java
    ".rb", ".php", ".go", ".java", ".kt",
    # Docker / CI
    "Dockerfile", ".dockerignore",
}

SKIP_DIRS: set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".tox", "dist", "build", ".mypy_cache", ".pytest_cache",
    ".eggs", "*.egg-info",
}

MAX_FILE_SIZE_BYTES: int = 1 * 1024 * 1024   # 1 MB — skip huge generated files

ALL_RULES: list[dict] = SECRET_RULES + CODE_RULES


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass
class AnalysisStats:
    files_scanned: int = 0
    lines_scanned: int = 0
    files_skipped: int = 0


def analyze_repository(repo_path: str) -> tuple[list[dict], AnalysisStats]:
    """
    Walk *repo_path* and run all rules against every scannable file.

    Returns:
        findings  – list of finding dicts (not yet DB objects)
        stats     – AnalysisStats with file / line counts
    """
    findings: list[dict] = []
    stats = AnalysisStats()

    for file_path in _walk_files(repo_path):
        try:
            file_findings, line_count = _scan_file(file_path, repo_path)
            findings.extend(file_findings)
            stats.files_scanned += 1
            stats.lines_scanned += line_count
        except (OSError, UnicodeDecodeError) as exc:
            logger.debug("Skipping %s: %s", file_path, exc)
            stats.files_skipped += 1

    logger.info(
        "Static analysis complete: %d findings in %d files (%d lines)",
        len(findings), stats.files_scanned, stats.lines_scanned,
    )
    return findings, stats


# ── Internal helpers ──────────────────────────────────────────────────────────

def _walk_files(base_path: str) -> Generator[Path, None, None]:
    """Yield every scannable file under *base_path*."""
    base = Path(base_path)
    for root, dirs, files in os.walk(base):
        # Prune skip directories in-place
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for filename in files:
            file_path = Path(root) / filename
            suffix    = file_path.suffix.lower()
            name      = file_path.name

            if suffix not in SCANNABLE_EXTENSIONS and name not in SCANNABLE_EXTENSIONS:
                continue
            if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                logger.debug("Skipping large file: %s", file_path)
                continue
            yield file_path


def _scan_file(file_path: Path, repo_root: str) -> tuple[list[dict], int]:
    """
    Apply all rules to a single file.

    Returns (findings, line_count).
    """
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines   = content.splitlines()
    rel_path = str(file_path.relative_to(repo_root))

    findings: list[dict] = []

    for lineno, line in enumerate(lines, start=1):
        for rule in ALL_RULES:
            match = rule["pattern"].search(line)
            if match:
                findings.append(_make_finding(rule, rel_path, lineno, line, match))

    return findings, len(lines)


def _make_finding(
    rule: dict,
    file_path: str,
    line_number: int,
    line: str,
    match: re.Match,
) -> dict:
    """Build a finding dict from a rule match."""
    # Redact the matched value to avoid storing raw secrets
    raw = match.group(0)
    redacted = _redact(raw)

    return {
        "rule_id":      rule["rule_id"],
        "title":        rule["title"],
        "description":  rule["description"],
        "severity":     rule["severity"],
        "finding_type": rule["finding_type"],
        "file_path":    file_path,
        "line_number":  line_number,
        "matched_text": redacted,
        "remediation":  rule.get("remediation"),
    }


def _redact(value: str) -> str:
    """Show only the first 6 and last 4 chars; mask the middle."""
    if len(value) <= 12:
        return "*" * len(value)
    return value[:6] + "*" * (len(value) - 10) + value[-4:]