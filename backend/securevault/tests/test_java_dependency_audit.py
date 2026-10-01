from types import SimpleNamespace

import requests

from app.models.scan import SeverityEnum
from app.services.scanner import dependency_auditor


def test_maven_dependencies_are_queried_as_coordinates_only(tmp_path, monkeypatch):
    (tmp_path / "pom.xml").write_text(
        """<project><dependencies>
        <dependency><groupId>org.example</groupId><artifactId>safe-lib</artifactId><version>1.2.3</version></dependency>
        <dependency><groupId>org.example</groupId><artifactId>managed-lib</artifactId><version>${managed.version}</version></dependency>
        </dependencies></project>""",
        encoding="utf-8",
    )
    requests_sent = []

    def fake_post(url, json, timeout):
        requests_sent.append((url, json, timeout))
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"results": [{"vulns": []}]},
        )

    monkeypatch.setattr(dependency_auditor.requests, "post", fake_post)

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["maven"] == "partial"
    assert len(requests_sent) == 1
    url, payload, timeout = requests_sent[0]
    assert url == dependency_auditor.OSV_QUERY_BATCH_URL
    assert payload == {
        "queries": [{
            "package": {"name": "org.example:safe-lib", "ecosystem": "Maven"},
            "version": "1.2.3",
        }]
    }
    assert timeout == dependency_auditor.OSV_TIMEOUT
    assert "managed.version" not in str(payload)


def test_osv_maven_vulnerability_becomes_dependency_finding(tmp_path, monkeypatch):
    (tmp_path / "pom.xml").write_text(
        """<project><dependencies>
        <dependency><groupId>org.example</groupId><artifactId>unsafe-lib</artifactId><version>1.2.3</version></dependency>
        </dependencies></project>""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dependency_auditor.requests,
        "post",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                "results": [{
                    "vulns": [{
                        "id": "GHSA-1234-5678-90ab",
                        "summary": "Example vulnerability",
                        "details": "A known issue.",
                        "aliases": ["CVE-2025-1234"],
                        "affected": [{
                            "ranges": [{"events": [{"fixed": "1.2.4"}]}]
                        }],
                    }]
                }]
            },
        ),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.coverage["maven"] == "checked"
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding["rule_id"] == "DEP-MAVEN-GHSA-1234-5678-90ab"
    assert finding["severity"] is SeverityEnum.MEDIUM
    assert finding["package_name"] == "org.example:unsafe-lib"
    assert finding["package_version"] == "1.2.3"
    assert finding["fix_version"] == "1.2.4"
    assert finding["file_path"] == "pom.xml"


def test_gradle_dynamic_versions_and_osv_outage_are_not_reported_clean(
    tmp_path, monkeypatch
):
    (tmp_path / "build.gradle.kts").write_text(
        """dependencies {
            implementation("org.example:exact-lib:2.0.0")
            implementation("org.example:dynamic-lib:3.+")
        }""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dependency_auditor.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.Timeout()),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["gradle"] == "partial"


def test_java_manifest_parse_failure_is_partial_and_does_not_call_osv(
    tmp_path, monkeypatch
):
    (tmp_path / "pom.xml").write_text("<!DOCTYPE project><project>", encoding="utf-8")
    monkeypatch.setattr(
        dependency_auditor.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("invalid XML must not reach OSV")
        ),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["maven"] == "partial"


def test_malformed_osv_response_is_reported_as_partial(tmp_path, monkeypatch):
    (tmp_path / "pom.xml").write_text(
        """<project><dependencies>
        <dependency><groupId>org.example</groupId><artifactId>safe-lib</artifactId><version>1.2.3</version></dependency>
        </dependencies></project>""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dependency_auditor.requests,
        "post",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"results": ["invalid-result"]},
        ),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["maven"] == "partial"
