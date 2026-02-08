from importlib.metadata import version

from cartography import _version as cartography_version


def get_cartography_version() -> str:
    """
    Return the current cartography release version.
    """
    return version("cartography")


def get_release_version_and_commit_revision() -> tuple[str, str]:
    """
    Return cartography release version and commit revision.
    """
    release_version = get_cartography_version()
    commit_revision = getattr(cartography_version, "__commit_id__", None)

    if not commit_revision:
        if "+g" in release_version:
            commit_revision = release_version.rsplit("+g", 1)[1]
        else:
            commit_revision = "unknown"

    return release_version, commit_revision
