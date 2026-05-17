"""
Repository cloner.
Uses GitPython to do a shallow clone (depth=1) of a remote repository
into an isolated temporary directory under CLONE_BASE_DIR.
The caller is responsible for clean-up (use the context manager).
"""
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from flask import current_app
from git import Repo, GitCommandError, InvalidGitRepositoryError

logger = logging.getLogger(__name__)


class CloneError(RuntimeError):
    """Raised when cloning fails for any reason."""


@contextmanager
def cloned_repo(repo_url: str, branch: str = "main") -> Generator[str, None, None]:
    """
    Context manager: clone *repo_url* at *branch* into a temp directory.

    Usage::
        with cloned_repo("https://github.com/org/repo", "main") as path:
            # path is the local directory
            ...
        # directory is deleted after the with-block

    Raises:
        CloneError on any git failure.
    """
    base_dir = current_app.config.get("CLONE_BASE_DIR", "/tmp/securevault_repos")
    os.makedirs(base_dir, exist_ok=True)

    clone_dir = tempfile.mkdtemp(dir=base_dir, prefix="sv_")
    logger.info("Cloning %s@%s → %s", repo_url, branch, clone_dir)

    try:
        Repo.clone_from(
            repo_url,
            clone_dir,
            branch=branch,
            depth=1,                        # shallow clone — faster, less disk
            multi_options=["--single-branch"],
        )
        _check_size(clone_dir)
        yield clone_dir
    except GitCommandError as exc:
        raise CloneError(f"Git clone failed: {exc}") from exc
    except InvalidGitRepositoryError as exc:
        raise CloneError(f"Invalid repository: {exc}") from exc
    finally:
        _cleanup(clone_dir)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_size(clone_dir: str):
    """Raise CloneError if the cloned repo exceeds the configured size limit."""
    max_mb = current_app.config.get("MAX_REPO_SIZE_MB", 500)
    total_bytes = sum(
        f.stat().st_size
        for f in Path(clone_dir).rglob("*")
        if f.is_file()
    )
    total_mb = total_bytes / (1024 * 1024)
    if total_mb > max_mb:
        raise CloneError(
            f"Repository size {total_mb:.1f} MB exceeds the limit of {max_mb} MB."
        )


def _cleanup(clone_dir: str):
    """Remove the clone directory, logging any errors."""
    try:
        shutil.rmtree(clone_dir, ignore_errors=True)
        logger.debug("Cleaned up clone dir: %s", clone_dir)
    except Exception as exc:
        logger.warning("Failed to clean up %s: %s", clone_dir, exc)