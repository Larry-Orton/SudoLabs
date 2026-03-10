"""Self-update logic for SudoLabs.

Pulls latest code from the GitHub remote and re-installs dependencies.
User data in ~/.sudolabs/ is never touched.
"""

import subprocess
import sys
from pathlib import Path

from sudolabs.config import PROJECT_ROOT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run a subprocess, return (returncode, combined output)."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode, output


def _is_git_repo(path: Path) -> bool:
    """Check if *path* is inside a Git working tree."""
    rc, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return rc == 0


def get_current_version() -> str:
    """Return the installed SudoLabs version string."""
    from sudolabs import __version__
    return __version__


def get_local_commit() -> str | None:
    """Return the short SHA of the current local HEAD."""
    if not _is_git_repo(PROJECT_ROOT):
        return None
    rc, out = _run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT)
    return out.strip() if rc == 0 else None


def get_remote_commit() -> str | None:
    """Fetch remote and return the short SHA of origin/main HEAD."""
    if not _is_git_repo(PROJECT_ROOT):
        return None
    _run(["git", "fetch", "origin", "main", "--quiet"], cwd=PROJECT_ROOT)
    rc, out = _run(
        ["git", "rev-parse", "--short", "origin/main"], cwd=PROJECT_ROOT
    )
    return out.strip() if rc == 0 else None


def check_for_update() -> tuple[bool, str | None, str | None]:
    """Check if an update is available.

    Returns (update_available, local_sha, remote_sha).
    """
    local = get_local_commit()
    remote = get_remote_commit()
    if local is None or remote is None:
        return False, local, remote
    return local != remote, local, remote


# ---------------------------------------------------------------------------
# Main update flow
# ---------------------------------------------------------------------------

def run_update(verbose: bool = True) -> bool:
    """Pull latest changes and re-install.

    Returns True on success, False on failure.
    """
    _print = print if verbose else (lambda *a, **k: None)

    # 1. Verify we're in a git repo
    if not _is_git_repo(PROJECT_ROOT):
        _print(f"  ✗ Not a git repository: {PROJECT_ROOT}")
        _print("    Re-clone from https://github.com/Larry-Orton/SudoLabs and re-install.")
        return False

    # 2. Check for uncommitted changes
    rc, status = _run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT)
    if status.strip():
        _print("  ✗ You have local modifications:")
        for line in status.strip().splitlines()[:10]:
            _print(f"    {line}")
        _print("    Stash or commit them first, then retry.")
        return False

    # 3. Pull latest
    _print("  Pulling latest changes...")
    rc, out = _run(["git", "pull", "origin", "main"], cwd=PROJECT_ROOT)
    if rc != 0:
        _print(f"  ✗ git pull failed:\n    {out}")
        return False

    if "Already up to date" in out:
        _print("  ✓ Already on the latest version.")
        return True

    _print(f"  ✓ {out.splitlines()[0]}")

    # 4. Re-install (picks up new deps from pyproject.toml / requirements.txt)
    _print("  Installing updated dependencies...")
    pip_exe = Path(sys.executable).parent / "pip"
    # Fall back to running pip as a module if the binary isn't found
    if pip_exe.exists():
        pip_cmd = [str(pip_exe), "install", "--quiet", "-e", str(PROJECT_ROOT)]
    else:
        pip_cmd = [sys.executable, "-m", "pip", "install", "--quiet", "-e", str(PROJECT_ROOT)]

    rc, out = _run(pip_cmd)
    if rc != 0:
        _print(f"  ✗ pip install failed:\n    {out}")
        return False

    _print("  ✓ Dependencies updated.")

    # 5. Run database migrations (safe — only applies pending ones)
    try:
        from sudolabs.db.database import init_db
        init_db()
        _print("  ✓ Database migrations applied.")
    except Exception as e:
        _print(f"  ! Migration warning: {e}")

    _print("")
    _print("  ✓ Update complete! Restart sudolabs to use the new version.")
    return True
