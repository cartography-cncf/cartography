import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

import cartography._version as cartography_version

logger = logging.getLogger(__name__)


def get_cartography_version() -> str:
    """
    Return the current cartography release version.
    """
    release_version, _ = get_release_version_and_commit_revision()
    return release_version


def get_release_version_and_commit_revision() -> tuple[str, str]:
    """
    Return cartography release version and commit revision.
    """
    try:
        release_version = version("cartography")
    except PackageNotFoundError:
        # In source/dev environments the package metadata may not be discoverable.
        logger.warning("cartography package not found. Returning 'dev' version.")
        release_version = "dev"
    commit_revision = getattr(cartography_version, "__commit_id__", None)

    if not commit_revision:
        if "+g" in release_version:
            commit_revision = release_version.rsplit("+g", 1)[1]
        else:
            commit_revision = "unknown"

    return release_version, commit_revision
