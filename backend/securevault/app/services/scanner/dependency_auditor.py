"""
Dependency auditor.
Detects requirements.txt / package.json and calls:
  - pip-audit  (Python)
  - npm audit  (Node.js)

Returns findings and per-ecosystem coverage compatible with scan_orchestrator.py.
"""
import json
import logging
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import requests

from app.models.scan import SeverityEnum, FindingTypeEnum

logger = logging.getLogger(__name__)

FINDING_TYPE = FindingTypeEnum.DEPENDENCY
OSV_QUERY_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT = (3, 10)
OSV_BATCH_SIZE = 100
MAX_OSV_PACKAGES = 1000
MAX_MANIFEST_SIZE_BYTES = 1024 * 1024
_EXACT_REQUIREMENT = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[A-Za-z0-9_,.-]+\])?"
    r"\s*==\s*([A-Za-z0-9][A-Za-z0-9.!+_-]*)$"
)
_EXACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MAVEN_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GRADLE_COORDINATE = re.compile(
    r"""["']([^:"'\s]+):([^:"'\s]+):([^"'\s]+)["']"""
)


class DependencyAuditError(RuntimeError):
    """Raised when repository dependency input cannot be audited safely."""


@dataclass
class DependencyAuditReport:
    findings: list[dict]
    coverage: dict[str, str]


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

def audit_dependencies(repo_path: str) -> DependencyAuditReport:
    """
    Audit Python, npm, Maven, and Gradle dependencies without building the repo.
    Coverage reports distinguish missing tools and unsupported manifests from clean checks.
    """
    findings: list[dict] = []
    base = Path(repo_path)
    coverage = {
        "python": "not_present",
        "npm": "not_present",
        "maven": "not_present",
        "gradle": "not_present",
    }

    for req_file in _manifest_paths(base, "requirements*.txt"):
        try:
            check_findings, status = _audit_pip_check(req_file)
        except DependencyAuditError as exc:
            logger.warning("Python dependency input is unsupported: %s", str(exc))
            check_findings, status = [], "partial"
        findings.extend(check_findings)
        coverage["python"] = _merge_coverage(coverage["python"], status)

    for pkg_file in _manifest_paths(base, "package.json"):
        check_findings, status = _audit_npm_check(pkg_file.parent)
        findings.extend(check_findings)
        coverage["npm"] = _merge_coverage(coverage["npm"], status)

    java_packages: list[dict] = []
    for pom_file in _manifest_paths(base, "pom.xml"):
        packages, status = _parse_maven_manifest(pom_file)
        for package in packages:
            package["manifest"] = (
                Path(package["manifest"]).resolve()
                .relative_to(base.resolve())
                .as_posix()
            )
        java_packages.extend(packages)
        coverage["maven"] = _merge_coverage(coverage["maven"], status)

    for gradle_file in (
        _manifest_paths(base, "build.gradle")
        + _manifest_paths(base, "build.gradle.kts")
    ):
        packages, status = _parse_gradle_manifest(gradle_file)
        for package in packages:
            package["manifest"] = (
                Path(package["manifest"]).resolve()
                .relative_to(base.resolve())
                .as_posix()
            )
        java_packages.extend(packages)
        coverage["gradle"] = _merge_coverage(coverage["gradle"], status)

    if java_packages:
        if len(java_packages) > MAX_OSV_PACKAGES:
            logger.warning("OSV dependency batch truncated at configured safety limit")
            for ecosystem_key in {item["coverage_key"] for item in java_packages}:
                coverage[ecosystem_key] = _merge_coverage(
                    coverage[ecosystem_key], "partial"
                )
            java_packages = java_packages[:MAX_OSV_PACKAGES]
        java_findings, java_status = _audit_osv_packages(java_packages)
        findings.extend(java_findings)
        for package in java_packages:
            ecosystem_key = package["coverage_key"]
            coverage[ecosystem_key] = _merge_coverage(
                coverage[ecosystem_key], java_status
            )

    logger.info("Dependency audit: %d findings", len(findings))
    return DependencyAuditReport(findings=findings, coverage=coverage)


def _manifest_paths(base: Path, pattern: str) -> list[Path]:
    resolved_base = base.resolve()
    return [
        path
        for path in base.rglob(pattern)
        if path.is_file()
        and not path.is_symlink()
        and "node_modules" not in path.parts
        and path.resolve().is_relative_to(resolved_base)
    ]


def _merge_coverage(current: str, incoming: str) -> str:
    if current == "not_present":
        return incoming
    if incoming == "not_present" or current == incoming:
        return current
    if "partial" in (current, incoming):
        return "partial"
    if "unavailable" in (current, incoming):
        return "partial"
    return "checked"


# ── pip-audit ─────────────────────────────────────────────────────────────────

def _audit_pip(requirements_file: Path) -> list[dict]:
    """Audit exact package pins without resolving or building repository packages."""
    return _audit_pip_check(requirements_file)[0]


def _audit_pip_check(requirements_file: Path) -> tuple[list[dict], str]:
    pinned_requirements = _read_exact_pins(requirements_file)
    with tempfile.TemporaryDirectory(prefix="securevault-pip-audit-") as temp_dir:
        safe_requirements = Path(temp_dir) / "pinned-requirements.txt"
        safe_requirements.write_text(
            "\n".join(pinned_requirements) + "\n",
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                [
                    "pip-audit",
                    "-r",
                    str(safe_requirements),
                    "--format",
                    "json",
                    "--no-progress",
                    "--no-deps",
                    "--disable-pip",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("pip-audit unavailable or timed out: %s", type(exc).__name__)
            return [], "unavailable"

    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        logger.warning("pip-audit returned non-JSON output")
        return [], "unavailable"
    if not isinstance(data, dict) or not isinstance(data.get("dependencies"), list):
        return [], "unavailable"

    findings: list[dict] = []
    for dep in data.get("dependencies", []):
        if not isinstance(dep, dict) or not isinstance(dep.get("vulns", []), list):
            return findings, "partial"
        for vuln in dep.get("vulns", []):
            if not isinstance(vuln, dict):
                continue
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
    return findings, "checked" if result.returncode in (0, 1) else "partial"


def _read_exact_pins(requirements_file: Path) -> list[str]:
    """Accept only package==version lines; reject includes and source references."""
    pinned_requirements = []
    for line in requirements_file.read_text(encoding="utf-8").splitlines():
        requirement = line.split("#", 1)[0].strip()
        if not requirement:
            continue
        match = _EXACT_REQUIREMENT.fullmatch(requirement)
        if match is None:
            raise DependencyAuditError(
                "Python dependency audit requires exact package==version pins; "
                "source references and requirement options are not supported."
            )
        pinned_requirements.append(f"{match.group(1)}=={match.group(2)}")

    if not pinned_requirements:
        raise DependencyAuditError(
            "Python dependency audit found no exact package==version pins."
        )
    return pinned_requirements


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
    return _audit_npm_check(package_dir)[0]


def _audit_npm_check(package_dir: Path) -> tuple[list[dict], str]:
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True, text=True, timeout=120,
            cwd=str(package_dir),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("npm audit unavailable or timed out: %s", type(exc).__name__)
        return [], "unavailable"

    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        logger.warning("npm audit returned non-JSON output")
        return [], "unavailable"
    if not isinstance(data, dict):
        return [], "unavailable"

    findings: list[dict] = []
    vulnerabilities = data.get("vulnerabilities", {})

    for pkg_name, vuln_info in vulnerabilities.items():
        if not isinstance(vuln_info, dict):
            return findings, "partial"
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
    return findings, "checked" if result.returncode in (0, 1) else "partial"


def _npm_fix_version(vuln_info: dict) -> str | None:
    fix = vuln_info.get("fixAvailable")
    if isinstance(fix, dict):
        return fix.get("version")
    return None


# ── Maven / Gradle manifests via OSV ─────────────────────────────────────────

def _parse_maven_manifest(manifest: Path) -> tuple[list[dict], str]:
    try:
        raw = manifest.read_bytes()
        if len(raw) > MAX_MANIFEST_SIZE_BYTES:
            return [], "partial"
        lowered = raw.lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            return [], "partial"
        root = ET.fromstring(raw)
    except (OSError, ET.ParseError):
        logger.warning("Could not parse Maven manifest: %s", manifest.name)
        return [], "partial"

    packages = []
    partial = False
    for dependency in root.iter():
        if dependency.tag.rsplit("}", 1)[-1] != "dependency":
            continue
        fields = {
            child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
            for child in dependency
        }
        group, artifact, version = (
            fields.get("groupId", ""),
            fields.get("artifactId", ""),
            fields.get("version", ""),
        )
        if not group and not artifact and not version:
            continue
        if (
            not _MAVEN_PART.fullmatch(group)
            or not _MAVEN_PART.fullmatch(artifact)
            or not _is_exact_version(version)
            or len(f"{group}:{artifact}") > 128
            or len(version) > 64
        ):
            partial = True
            continue
        packages.append({
            "name": f"{group}:{artifact}",
            "version": version,
            "manifest": manifest,
            "coverage_key": "maven",
        })
    return packages, "partial" if partial else "checked"


def _parse_gradle_manifest(manifest: Path) -> tuple[list[dict], str]:
    try:
        if manifest.stat().st_size > MAX_MANIFEST_SIZE_BYTES:
            return [], "partial"
        content = manifest.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        logger.warning("Could not read Gradle manifest: %s", manifest.name)
        return [], "partial"

    matches = list(_GRADLE_COORDINATE.finditer(content))
    dependency_declarations = len(re.findall(
        r"\b(?:api|implementation|compileOnly|runtimeOnly|"
        r"testImplementation|testRuntimeOnly|classpath)\s*(?:\(|\s)",
        content,
    ))
    partial = dependency_declarations > len(matches)
    packages = []
    for match in matches:
        group, artifact, version = match.groups()
        if (
            not _MAVEN_PART.fullmatch(group)
            or not _MAVEN_PART.fullmatch(artifact)
            or not _is_exact_version(version)
            or len(f"{group}:{artifact}") > 128
            or len(version) > 64
        ):
            partial = True
            continue
        packages.append({
            "name": f"{group}:{artifact}",
            "version": version,
            "manifest": manifest,
            "coverage_key": "gradle",
        })
    return packages, "partial" if partial else "checked"


def _is_exact_version(version: str) -> bool:
    return bool(_EXACT_VERSION.fullmatch(version)) and not version.lower().startswith(
        ("latest", "release")
    ) and not version.upper().endswith("-SNAPSHOT")


def _audit_osv_packages(packages: list[dict]) -> tuple[list[dict], str]:
    findings: list[dict] = []
    completed_batches = 0
    failed_batches = 0
    malformed_results = False

    for offset in range(0, len(packages), OSV_BATCH_SIZE):
        batch = packages[offset:offset + OSV_BATCH_SIZE]
        payload = {
            "queries": [
                {
                    "package": {"name": item["name"], "ecosystem": "Maven"},
                    "version": item["version"],
                }
                for item in batch
            ]
        }
        try:
            response = requests.post(
                OSV_QUERY_BATCH_URL,
                json=payload,
                timeout=OSV_TIMEOUT,
            )
            response.raise_for_status()
            results = response.json().get("results")
            if not isinstance(results, list) or len(results) != len(batch):
                raise ValueError("OSV returned an invalid batch response")
        except (requests.RequestException, ValueError, AttributeError) as exc:
            failed_batches += 1
            logger.warning("OSV dependency query failed: %s", type(exc).__name__)
            continue

        completed_batches += 1
        for package, result in zip(batch, results):
            if not isinstance(result, dict):
                malformed_results = True
                continue
            vulnerabilities = result.get("vulns", [])
            if not isinstance(vulnerabilities, list):
                malformed_results = True
                continue
            for vulnerability in vulnerabilities:
                if not isinstance(vulnerability, dict):
                    malformed_results = True
                    continue
                osv_id = vulnerability.get("id")
                if not isinstance(osv_id, str) or not osv_id:
                    malformed_results = True
                    continue
                aliases = vulnerability.get("aliases", [])
                cve_id = next(
                    (alias for alias in aliases if isinstance(alias, str) and alias.startswith("CVE-")),
                    None,
                ) if isinstance(aliases, list) else None
                description = (
                    vulnerability.get("summary")
                    or vulnerability.get("details")
                    or "OSV reports a known vulnerability for this package version."
                )
                if not isinstance(description, str):
                    description = "OSV reports a known vulnerability for this package version."
                    malformed_results = True
                findings.append({
                    "rule_id": f"DEP-MAVEN-{re.sub(r'[^A-Za-z0-9-]', '-', osv_id)[:64]}",
                    "title": f"Vulnerable Java package: {package['name']}",
                    "description": description[:2000],
                    "severity": _osv_severity(vulnerability),
                    "finding_type": FINDING_TYPE,
                    "file_path": str(package["manifest"]),
                    "line_number": None,
                    "matched_text": None,
                    "cve_id": cve_id,
                    "package_name": package["name"],
                    "package_version": package["version"],
                    "fix_version": _osv_fix_version(vulnerability),
                    "remediation": "Upgrade to a fixed version listed by OSV.",
                })

    if malformed_results or (failed_batches and completed_batches):
        return findings, "partial"
    if failed_batches:
        return findings, "unavailable"
    return findings, "checked"


def _osv_severity(vulnerability: dict) -> SeverityEnum:
    database_specific = vulnerability.get("database_specific")
    if not isinstance(database_specific, dict):
        return SeverityEnum.MEDIUM
    database_severity = database_specific.get("severity")
    if isinstance(database_severity, str):
        mapped = _PIP_SEVERITY_MAP.get(database_severity.upper())
        if mapped is not None:
            return mapped
        mapped = _NPM_SEVERITY_MAP.get(database_severity.lower())
        if mapped is not None:
            return mapped
    return SeverityEnum.MEDIUM


def _osv_fix_version(vulnerability: dict) -> str | None:
    affected_list = vulnerability.get("affected", [])
    if not isinstance(affected_list, list):
        return None
    for affected in affected_list:
        if not isinstance(affected, dict):
            continue
        for version_range in affected.get("ranges", []):
            if not isinstance(version_range, dict):
                continue
            for event in version_range.get("events", []):
                if isinstance(event, dict) and isinstance(event.get("fixed"), str):
                    return event["fixed"]
    return None