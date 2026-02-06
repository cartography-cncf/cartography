import logging
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

logger = logging.getLogger(__name__)


def get_version() -> str:
    """
    Get the current version of the cartography package.

    Returns the version string from the installed package metadata,
    or 'dev' if the package is not installed (e.g. development environments).
    """
    try:
        return version("cartography")
    except PackageNotFoundError:
        logger.debug("cartography package metadata not found, returning 'dev'.")
        return "dev"


def get_commit_hash() -> str | None:
    """
    Get the current git commit hash, if running from a git repository.

    Returns the short commit hash, or None if git is unavailable
    or this is not a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def get_version_string() -> str:
    """
    Get a formatted version string suitable for CLI output.

    Returns a string like "cartography, version 0.98.0 (commit: abc1234)"
    or "cartography, version 0.98.0" if git info is unavailable.
    """
    ver = get_version()
    commit = get_commit_hash()
    if commit:
        return f"cartography, version {ver} (commit: {commit})"
    return f"cartography, version {ver}"
