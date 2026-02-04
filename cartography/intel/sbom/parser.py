"""
CycloneDX SBOM parser for Cartography.

This module provides functions to parse and transform CycloneDX SBOMs
(from Syft) into DEPENDS_ON relationships between TrivyPackage nodes.

Package ID format matches Trivy's format: {version}|{name}
This enables the SBOM module to create relationships between TrivyPackage nodes.
"""

import logging
from typing import Any
from urllib.parse import unquote

logger = logging.getLogger(__name__)


def make_trivy_package_id(name: str, version: str) -> str:
    """
    Create a TrivyPackage ID in the format used by Trivy: {version}|{name}

    Args:
        name: Package name (e.g., "adduser", "lodash")
        version: Package version (e.g., "3.152", "4.17.21")

    Returns:
        Package ID in Trivy format (e.g., "3.152|adduser")
    """
    return f"{version}|{name}"


def extract_name_version_from_purl(purl: str) -> tuple[str, str] | None:
    """
    Extract package name and version from a purl (Package URL).

    Args:
        purl: Package URL string (e.g., "pkg:npm/lodash@4.17.21?qualifiers")

    Returns:
        Tuple of (name, version) or None if extraction fails.
    """
    if not purl:
        return None

    # Decode URL-encoded characters
    decoded_purl = unquote(purl)

    # purl format: pkg:type/namespace/name@version?qualifiers#subpath
    # or pkg:type/name@version?qualifiers#subpath (no namespace)

    # Strip query parameters and subpath
    purl_base = decoded_purl.split("?")[0].split("#")[0]

    if "@" not in purl_base:
        return None

    # Split on @ to get name part and version
    parts = purl_base.rsplit("@", 1)
    if len(parts) != 2:
        return None

    name_part, version = parts

    # Extract just the name (last segment after /)
    name = name_part.split("/")[-1]

    if not name or not version:
        return None

    return name, version


def validate_cyclonedx_sbom(sbom_data: dict[str, Any]) -> bool:
    """
    Validate that the provided data is a valid CycloneDX SBOM.

    Args:
        sbom_data: Raw SBOM data as a dictionary.

    Returns:
        True if the SBOM is valid, False otherwise.
    """
    if not isinstance(sbom_data, dict):
        logger.warning("SBOM data is not a dictionary")
        return False

    # Check for required CycloneDX fields
    if "bomFormat" not in sbom_data:
        logger.warning("SBOM missing 'bomFormat' field")
        return False

    if sbom_data.get("bomFormat") != "CycloneDX":
        logger.warning(
            "SBOM bomFormat is '%s', expected 'CycloneDX'",
            sbom_data.get("bomFormat"),
        )
        return False

    if "specVersion" not in sbom_data:
        logger.warning("SBOM missing 'specVersion' field")
        return False

    # Components are required for meaningful processing
    if "components" not in sbom_data or not sbom_data["components"]:
        logger.warning("SBOM has no components")
        return False

    return True


def transform_sbom_dependencies(
    sbom_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform SBOM dependency graph into relationship data for MatchLinks.

    Creates data for DEPENDS_ON relationships between TrivyPackage nodes.
    Package IDs use Trivy format: {version}|{name}

    Args:
        sbom_data: CycloneDX SBOM data.

    Returns:
        List of dictionaries for DEPENDS_ON relationships with Trivy-compatible IDs.
    """
    dependencies = sbom_data.get("dependencies", [])
    components = sbom_data.get("components", [])

    # Build a mapping from bom-ref to Trivy package ID
    bom_ref_to_id: dict[str, str] = {}
    for component in components:
        bom_ref = component.get("bom-ref", "")
        if not bom_ref:
            continue

        purl = component.get("purl")
        name = component.get("name", "")
        version = component.get("version", "")

        # Try to extract name and version from purl if not provided
        if purl and (not name or not version):
            extracted = extract_name_version_from_purl(purl)
            if extracted:
                name, version = extracted

        # Skip components without name or version
        if not name or not version:
            continue

        # Generate ID in Trivy format: {version}|{name}
        pkg_id = make_trivy_package_id(name, version)
        bom_ref_to_id[bom_ref] = pkg_id

    # Build dependency relationships
    dep_relationships = []
    for dep_entry in dependencies:
        source_ref = dep_entry.get("ref", "")
        if source_ref not in bom_ref_to_id:
            continue

        source_id = bom_ref_to_id[source_ref]
        depends_on_refs = dep_entry.get("dependsOn", [])

        for target_ref in depends_on_refs:
            if target_ref not in bom_ref_to_id:
                continue

            target_id = bom_ref_to_id[target_ref]
            dep_relationships.append(
                {
                    "source_id": source_id,
                    "depends_on_id": target_id,
                }
            )

    logger.debug("Transformed %d dependency relationships", len(dep_relationships))
    return dep_relationships
