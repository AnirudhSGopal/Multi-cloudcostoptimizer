"""
Dependency auditor.
Detects requirements.txt / package.json and calls:
  - pip-audit  (Python)
  - npm audit  (Node.js)

Returns a list of finding dicts compatible with scan_orchestrator.py.
"""
import json
import logging
import subprocess
from pathlib import Path

from app.models.scan import SeverityEnum, FindingTypeEnum

logger = logging.getLogger(__name__)

FINDING_TYPE = FindingTypeEnum.DEPENDENCY

# ── Severity mapping ──────────────────────────────────────────────────────────

_NPM_SEVERITY_MAP: dict[str, SeverityEnum] = {
    "critical": SeverityEnum.CRITICAL,
    "high":     SeverityEnum.HIGH,
    "moderate": SeverityEnum.MEDIUM,
    "medium":   SeverityEnum.MEDIUM,
    "low":      SeverityEnum.LOW,
    "info":     SeverityEnum.INFO,
}

_PIP_SEVERITY_MAP: dict[str, SeverityEnum] = {
    "CRITICAL": SeverityEnum.CRITICAL,
    "HIGH":     SeverityEnum.HIGH,
    "MODERATE": SeverityEnum.MEDIUM,
    "MEDIUM":   SeverityEnum.MEDIUM,
    "LOW":      SeverityEnum.LOW,
}


# ── Public API ────────────────────────────────────────────────────────────────

def audit_dependencies(repo_path: str) -> list[dict]:
    """
    Audit Python and Node.js dependencies found in *repo_path*.
    Returns a merged list of finding dicts.
    """
    findings: list[dict] = []
    base = Path(repo_path)

    for req_file in base.rglob("requirements*.txt"):
        findings.extend(_audit_pip(req_file))

    for pkg_file in base.rglob("package.json"):
        if "node_modules" in pkg_file.parts:
            continue
        findings.extend(_audit_npm(pkg_file.parent))

    logger.info("Dependency audit: %d findings", len(findings))
    return findings


# ── pip-audit ─────────────────────────────────────────────────────────────────

def _audit_pip(requirements_file: Path) -> list[dict]:
    """Run pip-audit against a requirements file and parse JSON output."""
    logger.debug("Running pip-audit on %s", requirements_file)
    try:
        result = subprocess.run(
            ["pip-audit", "-r", str(requirements_file), "--format", "json", "--no-progress"],
            capture_output=True, text=True, timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("pip-audit unavailable or timed out: %s", exc)
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("pip-audit returned non-JSON output: %s", result.stdout[:200])
        return []

    findings: list[dict] = []
    for dep in data.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            severity = _pip_severity(vuln)
            findings.append({
                "rule_id":       f"DEP-PY-{vuln.get('id', 'UNKNOWN')}",
                "title":         f"Vulnerable Python package: {dep['name']}",
                "description":   vuln.get("description", "No description available."),
                "severity":      severity,
                "finding_type":  FINDING_TYPE,
                "file_path":     str(requirements_file),
                "line_number":   None,
                "matched_text":  None,
                "cve_id":        vuln.get("aliases", [None])[0],
                "package_name":  dep["name"],
                "package_version": dep.get("version"),
                "fix_version":   _pip_fix_version(vuln),
                "remediation":   (
                    f"Upgrade {dep['name']} to a patched version. "
                    f"See {vuln.get('fix_versions', [])}."
                ),
            })
    return findings


def _pip_severity(vuln: dict) -> SeverityEnum:
    aliases = vuln.get("aliases", [])
    # pip-audit doesn't always include CVSS; default to HIGH for CVEs
    if any(a.startswith("CVE-") for a in aliases):
        return SeverityEnum.HIGH
    return SeverityEnum.MEDIUM


def _pip_fix_version(vuln: dict) -> str | None:
    versions = vuln.get("fix_versions", [])
    return versions[0] if versions else None


# ── npm audit ─────────────────────────────────────────────────────────────────

def _audit_npm(package_dir: Path) -> list[dict]:
    """Run npm audit in *package_dir* and parse JSON output."""
    logger.debug("Running npm audit in %s", package_dir)
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True, text=True, timeout=120,
            cwd=str(package_dir),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("npm audit unavailable or timed out: %s", exc)
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("npm audit returned non-JSON output: %s", result.stdout[:200])
        return []

    findings: list[dict] = []
    vulnerabilities = data.get("vulnerabilities", {})

    for pkg_name, vuln_info in vulnerabilities.items():
        severity_str = vuln_info.get("severity", "low")
        severity = _NPM_SEVERITY_MAP.get(severity_str, SeverityEnum.LOW)

        for via in vuln_info.get("via", []):
            if not isinstance(via, dict):
                continue
            findings.append({
                "rule_id":       f"DEP-JS-{via.get('source', pkg_name)}",
                "title":         f"Vulnerable npm package: {pkg_name}",
                "description":   via.get("title", "No description."),
                "severity":      severity,
                "finding_type":  FINDING_TYPE,
                "file_path":     str(package_dir / "package.json"),
                "line_number":   None,
                "matched_text":  None,
                "cve_id":        via.get("cve"),
                "package_name":  pkg_name,
                "package_version": vuln_info.get("range"),
                "fix_version":   _npm_fix_version(vuln_info),
                "remediation":   via.get("url", "Run `npm audit fix` to patch."),
            })
    return findings


def _npm_fix_version(vuln_info: dict) -> str | None:
    fix = vuln_info.get("fixAvailable")
    if isinstance(fix, dict):
        return fix.get("version")
    return None