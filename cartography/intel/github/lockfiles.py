"""
Pure lockfile parsers used by the GitHub dependency-graph fallback.

GitHub's dependency graph reports some dependencies with only a version range
(no exact version). When a repo also ships a lockfile we can parse, we recover
the exact version from it. These functions are pure: they take file contents and
return a mapping of package name to exact version, with no network access.

Both parsers only return versions that are unambiguous for a *direct* manifest
dependency:

- npm: only top-level installs (``node_modules/<name>``) are returned. Nested
  transitive installs (``node_modules/a/node_modules/b``) are ignored, so a
  transitive version can never be attached to a direct dependency of the same
  name.
- uv: a package name that resolves to more than one distinct version is dropped
  rather than guessing which version a range refers to.
"""

import json
import logging
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10: tomllib is not in the stdlib yet.
    import tomli as tomllib

logger = logging.getLogger(__name__)


def parse_uv_lock(content: str) -> dict[str, str]:
    """
    Parse a uv.lock file into a mapping of package name to exact version.

    uv.lock is a TOML file with one ``[[package]]`` table per locked package,
    each carrying a ``name`` and an exact ``version``. If a name resolves to more
    than one distinct version, it is dropped as ambiguous.

    :param content: The raw uv.lock file contents.
    :return: A mapping of package name to exact version. Empty if the content
        cannot be parsed.
    """
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        logger.warning("Failed to parse uv.lock content; skipping lockfile fallback.")
        return {}

    versions_by_name: dict[str, set[str]] = {}
    for package in data.get("package") or []:
        if not isinstance(package, dict):
            continue
        name = package.get("name")
        version = package.get("version")
        # Skip malformed entries rather than crashing: name/version must be
        # non-empty strings before being used as a dict key / set member.
        if isinstance(name, str) and name and isinstance(version, str) and version:
            versions_by_name.setdefault(name, set()).add(version)

    return {
        name: next(iter(versions))
        for name, versions in versions_by_name.items()
        if len(versions) == 1
    }


def parse_npm_lock(content: str) -> dict[str, str]:
    """
    Parse a package-lock.json file into a mapping of package name to exact version.

    Only top-level (direct) installs are returned, so a transitive version is
    never attached to a direct dependency of the same name:

    - v2/v3 ``packages`` layout: only keys of the form ``node_modules/<name>``
      (a single ``node_modules/`` segment) are used; deeper, nested install
      paths are ignored.
    - legacy v1 ``dependencies`` layout: only the top-level entries are used;
      their nested ``dependencies`` are not traversed.

    The v2/v3 layout wins when both are present.

    :param content: The raw package-lock.json file contents.
    :return: A mapping of package name to exact version. Empty if the content
        cannot be parsed.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse package-lock.json content; skipping lockfile fallback.",
        )
        return {}

    versions: dict[str, str] = {}

    # v2/v3: `packages` keyed by install path. Top-level installs have exactly
    # one `node_modules/` segment; the root project has key "".
    packages = data.get("packages")
    if isinstance(packages, dict):
        for path, info in packages.items():
            if not path or not isinstance(info, dict):
                continue
            if not path.startswith("node_modules/"):
                continue
            if path.count("node_modules/") != 1:
                # Nested transitive install (e.g. node_modules/a/node_modules/b).
                continue
            name = path[len("node_modules/") :]
            version = info.get("version")
            if name and isinstance(version, str) and version:
                versions[name] = version

    # Legacy v1: only the top-level `dependencies` entries are direct deps.
    if not versions:
        dependencies = data.get("dependencies")
        if isinstance(dependencies, dict):
            for name, info in dependencies.items():
                if not isinstance(info, dict):
                    continue
                version = info.get("version")
                if name and isinstance(version, str) and version:
                    versions[name] = version

    return versions
