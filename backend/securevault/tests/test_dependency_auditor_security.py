import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.services.scanner import dependency_auditor


def test_pip_audit_rejects_repository_controlled_package_sources(
    tmp_path, monkeypatch
):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("-e .\n", encoding="utf-8")

    def unexpected_subprocess(*args, **kwargs):
        pytest.fail("untrusted requirements must not reach pip-audit")

    monkeypatch.setattr(dependency_auditor.subprocess, "run", unexpected_subprocess)

    with pytest.raises(dependency_auditor.DependencyAuditError):
        dependency_auditor._audit_pip(requirements)


def test_pip_audit_uses_only_exact_pins_without_invoking_pip(
    tmp_path, monkeypatch
):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "requests==2.31.0  # pinned\nflask[async]==3.1.3\n",
        encoding="utf-8",
    )
    invocation = {}

    def inspect_subprocess(args, **kwargs):
        invocation["args"] = args
        invocation["requirements"] = Path(args[2]).read_text(encoding="utf-8")
        return SimpleNamespace(stdout='{"dependencies": []}', returncode=0)

    monkeypatch.setattr(dependency_auditor.subprocess, "run", inspect_subprocess)

    assert dependency_auditor._audit_pip(requirements) == []
    assert invocation["args"][:2] == ["pip-audit", "-r"]
    assert invocation["args"][-2:] == ["--no-deps", "--disable-pip"]
    assert invocation["requirements"] == "requests==2.31.0\nflask==3.1.3\n"
    assert str(requirements) not in invocation["args"]


def test_unavailable_pip_audit_is_reported_as_unavailable_coverage(
    tmp_path, monkeypatch
):
    (tmp_path / "requirements.txt").write_text(
        "requests==2.31.0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dependency_auditor.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["python"] == "unavailable"


def test_unsupported_python_pins_are_partial_instead_of_clean(
    tmp_path, monkeypatch
):
    (tmp_path / "requirements.txt").write_text(
        "unsafe-package>=1.0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        dependency_auditor.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail(
            "unsupported requirements must not reach pip-audit"
        ),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["python"] == "partial"


def test_unavailable_npm_audit_is_reported_as_unavailable_coverage(
    tmp_path, monkeypatch
):
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    monkeypatch.setattr(
        dependency_auditor.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )

    report = dependency_auditor.audit_dependencies(str(tmp_path))

    assert report.findings == []
    assert report.coverage["npm"] == "unavailable"


@pytest.mark.parametrize(
    "line",
    [
        "requests>=2.31.0",
        "git+https://example.invalid/project.git#egg=unsafe",
        "--find-links ./packages",
        "-r included-requirements.txt",
    ],
)
def test_pip_audit_rejects_unpinned_or_indirect_requirement_syntax(
    tmp_path, monkeypatch, line
):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(f"{line}\n", encoding="utf-8")
    monkeypatch.setattr(
        dependency_auditor.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail(
            "unsupported requirements must not reach pip-audit"
        ),
    )

    with pytest.raises(dependency_auditor.DependencyAuditError):
        dependency_auditor._audit_pip(requirements)
