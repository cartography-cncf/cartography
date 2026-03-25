"""
GitLab Manifest File Parser

Parses dependency manifest files to extract version constraints (requirements).
This provides parity with GitHub's DependencyGraphManifest which includes
the `requirements` field showing version pins/constraints.

Supported formats:
- requirements.txt (Python PEP 508)
- Pipfile (Python)
- package.json (Node.js)
- go.mod (Go)
- Gemfile (Ruby)
- pom.xml (Java/Maven)
"""

import json
import logging
import re
from typing import Any

import requests

from cartography.intel.gitlab.util import check_rate_limit_remaining
from cartography.intel.gitlab.util import make_request_with_retry

logger = logging.getLogger(__name__)

# Manifest filenames we can parse for version constraints
PARSEABLE_MANIFESTS = {
    "requirements.txt",
    "Pipfile",
    "package.json",
    "go.mod",
    "Gemfile",
}


def fetch_manifest_contents(
    gitlab_url: str,
    token: str,
    project_id: int,
    file_path: str,
    default_branch: str = "main",
) -> str | None:
    """
    Fetch raw file contents from a GitLab repository.

    :param gitlab_url: GitLab instance URL.
    :param token: GitLab API token.
    :param project_id: Numeric project ID.
    :param file_path: Path to the file in the repository.
    :param default_branch: Branch to fetch from.
    :return: File contents as string, or None on error.
    """
    headers = {
        "Authorization": f"Bearer {token}",
    }

    # URL-encode the file path for the API
    encoded_path = file_path.replace("/", "%2F")
    url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw"
    params = {"ref": default_branch}

    try:
        response = make_request_with_retry("GET", url, headers, params)

        if response.status_code == 404:
            logger.debug(f"File not found: {file_path}")
            return None

        response.raise_for_status()
        check_rate_limit_remaining(response)
        return response.text

    except requests.exceptions.RequestException as e:
        logger.debug(f"Error fetching file {file_path}: {e}")
        return None


def parse_requirements_txt(content: str) -> dict[str, str]:
    """
    Parse a requirements.txt file to extract package name -> version constraint mappings.

    Handles:
    - Pinned versions: requests==2.31.0
    - Version ranges: Flask>=2.0,<3.0
    - Compatible releases: Django~=4.2
    - Comments and blank lines
    - -r/-c includes (skipped)
    - Environment markers (stripped)

    :return: Dict mapping lowercase package name to constraint string.
    """
    constraints: dict[str, str] = {}

    for line in content.splitlines():
        line = line.strip()

        # Skip empty lines, comments, and flags
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Strip inline comments
        if " #" in line:
            line = line[: line.index(" #")].strip()

        # Strip environment markers (e.g., ; python_version >= "3.8")
        if ";" in line:
            line = line[: line.index(";")].strip()

        # Match package name and version specifier
        # PEP 508: name followed by version specifiers
        match = re.match(
            r"^([A-Za-z0-9][\w.\-]*)\s*(.*)",
            line,
        )
        if match:
            pkg_name = match.group(1).strip()
            version_spec = match.group(2).strip()

            if version_spec:
                # Normalize: canonicalize the package name
                canonical = _canonicalize_python_name(pkg_name)
                constraints[canonical] = version_spec

    return constraints


def parse_pipfile(content: str) -> dict[str, str]:
    """
    Parse a Pipfile to extract package name -> version constraint mappings.

    Handles the [packages] and [dev-packages] sections in TOML-like format.
    Pipfile uses a simplified TOML format.

    :return: Dict mapping lowercase package name to constraint string.
    """
    constraints: dict[str, str] = {}
    in_packages_section = False

    for line in content.splitlines():
        stripped = line.strip()

        # Track sections
        if stripped.startswith("["):
            in_packages_section = stripped in ("[packages]", "[dev-packages]")
            continue

        if not in_packages_section or not stripped or stripped.startswith("#"):
            continue

        # Parse key = value pairs
        if "=" in stripped:
            parts = stripped.split("=", 1)
            pkg_name = parts[0].strip().strip('"')
            version_spec = parts[1].strip().strip('"')

            # Skip wildcard versions ("*")
            if version_spec == "*":
                continue

            canonical = _canonicalize_python_name(pkg_name)
            constraints[canonical] = version_spec

    return constraints


def parse_package_json(content: str) -> dict[str, str]:
    """
    Parse a package.json file to extract package name -> version constraint mappings.

    Combines dependencies and devDependencies.

    :return: Dict mapping package name to constraint string.
    """
    constraints: dict[str, str] = {}

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return constraints

    for section in ("dependencies", "devDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            for name, version in deps.items():
                if isinstance(version, str):
                    constraints[name.lower()] = version

    return constraints


def parse_go_mod(content: str) -> dict[str, str]:
    """
    Parse a go.mod file to extract module name -> version constraint mappings.

    :return: Dict mapping module name to version string.
    """
    constraints: dict[str, str] = {}
    in_require_block = False

    for line in content.splitlines():
        stripped = line.strip()

        # Handle require block
        if stripped == "require (":
            in_require_block = True
            continue
        if stripped == ")":
            in_require_block = False
            continue

        # Single-line require
        if stripped.startswith("require ") and "(" not in stripped:
            parts = stripped.split()
            if len(parts) >= 3:
                module_name = parts[1]
                version = parts[2]
                constraints[module_name.lower()] = version
            continue

        # Inside require block
        if in_require_block and stripped and not stripped.startswith("//"):
            parts = stripped.split()
            if len(parts) >= 2:
                module_name = parts[0]
                version = parts[1]
                # Strip // indirect comment
                constraints[module_name.lower()] = version

    return constraints


def parse_gemfile(content: str) -> dict[str, str]:
    """
    Parse a Gemfile to extract gem name -> version constraint mappings.

    :return: Dict mapping gem name to constraint string.
    """
    constraints: dict[str, str] = {}

    for line in content.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Match gem 'name', 'version_constraint'
        match = re.match(
            r"""gem\s+['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]""",
            stripped,
        )
        if match:
            gem_name = match.group(1)
            version_spec = match.group(2)
            constraints[gem_name.lower()] = version_spec

    return constraints


def _canonicalize_python_name(name: str) -> str:
    """Canonicalize a Python package name per PEP 503."""
    try:
        from packaging.utils import canonicalize_name
        return str(canonicalize_name(name))
    except ImportError:
        return re.sub(r"[._-]+", "-", name.lower())


# Map filenames to their parser functions
_PARSERS: dict[str, Any] = {
    "requirements.txt": parse_requirements_txt,
    "Pipfile": parse_pipfile,
    "package.json": parse_package_json,
    "go.mod": parse_go_mod,
    "Gemfile": parse_gemfile,
}


def fetch_and_parse_manifests(
    gitlab_url: str,
    token: str,
    project_id: int,
    dependency_files: list[dict[str, Any]],
    default_branch: str = "main",
) -> dict[str, dict[str, str]]:
    """
    Fetch and parse manifest files to extract version constraints.

    :param gitlab_url: GitLab instance URL.
    :param token: GitLab API token.
    :param project_id: Numeric project ID.
    :param dependency_files: Transformed dependency files list.
    :param default_branch: Branch to fetch files from.
    :return: Dict mapping manifest_path -> {canonical_pkg_name -> version_constraint}.
    """
    requirements_by_manifest: dict[str, dict[str, str]] = {}

    for dep_file in dependency_files:
        filename = dep_file.get("filename", "")
        file_path = dep_file.get("path", "")

        parser = _PARSERS.get(filename)
        if not parser:
            continue

        content = fetch_manifest_contents(
            gitlab_url, token, project_id, file_path, default_branch,
        )
        if not content:
            continue

        try:
            constraints = parser(content)
            if constraints:
                requirements_by_manifest[file_path] = constraints
                logger.debug(
                    f"Parsed {len(constraints)} constraints from {file_path}",
                )
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")

    return requirements_by_manifest
