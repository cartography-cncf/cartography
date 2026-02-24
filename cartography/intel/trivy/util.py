"""
Utility functions for Trivy module.

This module provides package normalization functions following ecosystem-specific
rules (PEP 503 for Python, lowercase for others) to enable cross-tool matching.
"""

import re

from packageurl import PackageURL


def normalize_package_name(name: str, pkg_type: str) -> str:
    """
    Normalize package name based on ecosystem rules.

    Args:
        name: Package name
        pkg_type: Package type (python, pypi, npm, deb, etc.)

    Returns:
        Normalized package name
    """
    pkg_type_lower = pkg_type.lower() if pkg_type else ""

    if pkg_type_lower in ("python", "pypi", "python-pkg"):
        # PEP 503: lowercase, replace runs of [._-] with single dash
        return re.sub(r"[._-]+", "-", name.lower())
    elif pkg_type_lower in ("npm", "node", "node-pkg"):
        # npm: lowercase
        return name.lower()
    else:
        # deb, apk, etc: lowercase
        return name.lower()


def parse_purl(purl: str | None) -> dict | None:
    """
    Parse PURL into components.

    Args:
        purl: Package URL string (e.g., "pkg:pypi/requests@2.28.0")

    Returns:
        Dictionary with type, namespace, name, version, or None if invalid
    """
    if not purl:
        return None

    try:
        parsed = PackageURL.from_string(purl)
    except ValueError:
        return None

    return {
        "type": parsed.type,
        "namespace": parsed.namespace,
        "name": parsed.name,
        "version": parsed.version,
    }


def make_normalized_package_id(
    purl: str | None = None,
    name: str | None = None,
    version: str | None = None,
    pkg_type: str | None = None,
) -> str | None:
    """
    Create a normalized package ID for cross-tool matching.

    The ID format is: {type}|{namespace/}{normalized_name}|{version}

    The namespace is included when present to avoid collisions between
    packages like pkg:npm/%40types/node@18.0.0 and pkg:npm/node@18.0.0.

    This enables matching packages between Trivy and Syft despite:
    - Case differences (PyNaCl vs pynacl)
    - Separator differences (jaraco.context vs jaraco-context)
    - Ecosystem conflicts (npm lodash vs pip lodash)

    Args:
        purl: Package URL (preferred, used to extract all components)
        name: Package name (fallback if no PURL)
        version: Package version (fallback if no PURL)
        pkg_type: Package type (fallback if no PURL)

    Returns:
        Normalized ID in format "{type}|{namespace/}{normalized_name}|{version}" or None
    """
    if purl:
        parsed = parse_purl(purl)
        if parsed and parsed["name"] and parsed["version"]:
            norm_name = normalize_package_name(parsed["name"], parsed["type"])
            ns_prefix = f"{parsed['namespace']}/" if parsed.get("namespace") else ""
            return f"{parsed['type']}|{ns_prefix}{norm_name}|{parsed['version']}"

    # Fallback to provided components
    if name and version and pkg_type:
        norm_name = normalize_package_name(name, pkg_type)
        pkg_type_lower = pkg_type.lower() if pkg_type else "unknown"
        return f"{pkg_type_lower}|{norm_name}|{version}"

    return None
