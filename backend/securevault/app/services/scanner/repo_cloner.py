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
def cloned_repo(repo_url: str) -> Generator[str, None, None]:
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
    base_dir = current_app.config.get("CLONE_BASE_DIR")
    if not base_dir or base_dir.startswith("/tmp"):
        base_dir = os.path.join(tempfile.gettempdir(), "securevault_repos")
    os.makedirs(base_dir, exist_ok=True)

    clone_dir = tempfile.mkdtemp(dir=base_dir, prefix="sv_")
    os.rmdir(clone_dir) # git clone needs to create the directory itself

    # Inject GitHub token for private repos if available
    github_token = current_app.config.get("GITHUB_TOKEN")
    if github_token and github_token != "your_github_token_here" and "github.com" in repo_url and "@github.com" not in repo_url:
        repo_url = repo_url.replace("https://github.com/", f"https://{github_token}@github.com/")

    logger.info("Cloning %s -> %s", repo_url, clone_dir)

    try:
        Repo.clone_from(
            repo_url,
            clone_dir,
            depth=1,                        # shallow clone - faster, less disk
            env={"GIT_TERMINAL_PROMPT": "0"}
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
    
    # Highly optimized size calculation: skip .git and node_modules on Windows
    total_bytes = 0
    ignore_dirs = {'.git', 'node_modules', 'venv', '.venv'}
    for root, dirs, filenames in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for fname in filenames:
            fpath = os.path.join(root, fname)
            try:
                total_bytes += os.path.getsize(fpath)
            except Exception:
                pass
                
    total_mb = total_bytes / (1024 * 1024)
    if total_mb > max_mb:
        raise CloneError(
            f"Repository size {total_mb:.1f} MB exceeds the limit of {max_mb} MB."
        )


def _cleanup(clone_dir: str):
    """Remove the clone directory, handling Windows read-only file lock issues."""
    import stat
    def remove_readonly(func, path, excinfo):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    try:
        shutil.rmtree(clone_dir, onerror=remove_readonly)
        logger.debug("Cleaned up clone dir: %s", clone_dir)
    except Exception as exc:
        logger.warning("Failed to clean up %s: %s", clone_dir, exc)