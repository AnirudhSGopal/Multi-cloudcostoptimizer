import pytest
from pathlib import Path

from app.core.factory import create_app
from app.services.scanner import repo_cloner
from app.services.scanner.repo_cloner import CloneError, validate_repo_url


def test_repository_url_accepts_only_a_github_https_repository():
    assert (
        validate_repo_url("https://github.com/acme/service.git")
        == "https://github.com/acme/service.git"
    )


@pytest.mark.parametrize(
    "repo_url",
    [
        "-oProxyCommand=evil",
        "http://github.com/acme/service",
        "https://user:password@github.com/acme/service",
        "https://127.0.0.1/acme/service",
        "https://[::1]/acme/service",
        "https://localhost/acme/service",
        "https://169.254.169.254/acme/service",
        "https://github.com.evil.example/acme/service",
        "https://github.com/acme/service?token=secret",
    ],
)
def test_repository_url_rejects_untrusted_or_option_like_values(repo_url):
    with pytest.raises(CloneError):
        validate_repo_url(repo_url)


def test_clone_keeps_token_out_of_url_and_logs_and_cleans_temp_directory(
    monkeypatch, tmp_path, caplog
):
    app = create_app("testing")
    app.config.update(CLONE_BASE_DIR=str(tmp_path), GITHUB_TOKEN="token-for-test")
    captured = {}

    def fake_clone(url, target, **kwargs):
        captured["url"] = url
        captured["env"] = kwargs.get("env")
        Path(target).mkdir(exist_ok=True)
        (Path(target) / "marker").touch()

    monkeypatch.setattr(repo_cloner.Repo, "clone_from", fake_clone)

    with app.app_context():
        with repo_cloner.cloned_repo("https://github.com/acme/service.git") as clone_dir:
            assert (Path(clone_dir) / "marker").exists()
            cloned_path = clone_dir

    assert captured["url"] == "https://github.com/acme/service.git"
    assert "token-for-test" not in captured["url"]
    assert "token-for-test" not in caplog.text
    assert cloned_path.startswith(str(tmp_path))
    assert not Path(cloned_path).exists()


def test_clone_uses_requested_branch(monkeypatch, tmp_path):
    app = create_app("testing")
    app.config["CLONE_BASE_DIR"] = str(tmp_path)
    captured = {}

    def fake_clone(url, target, **kwargs):
        captured["branch"] = kwargs.get("branch")
        Path(target).mkdir(exist_ok=True)

    monkeypatch.setattr(repo_cloner.Repo, "clone_from", fake_clone)

    with app.app_context():
        with repo_cloner.cloned_repo(
            "https://github.com/acme/service.git", branch="release/2026"
        ):
            pass

    assert captured["branch"] == "release/2026"


@pytest.mark.parametrize("branch", ["-c core.sshCommand=evil", "../main", "main\n--upload-pack=evil"])
def test_clone_rejects_option_like_or_unsafe_branch(monkeypatch, tmp_path, branch):
    app = create_app("testing")
    app.config["CLONE_BASE_DIR"] = str(tmp_path)
    monkeypatch.setattr(
        repo_cloner.Repo,
        "clone_from",
        lambda *args, **kwargs: pytest.fail("unsafe branch reached git"),
    )

    with app.app_context(), pytest.raises(CloneError):
        with repo_cloner.cloned_repo("https://github.com/acme/service.git", branch=branch):
            pass
