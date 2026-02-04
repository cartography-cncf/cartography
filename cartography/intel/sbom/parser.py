"""
CycloneDX SBOM parser for Cartography.

This module provides functions to parse and transform CycloneDX SBOMs
(from Syft) to enrich existing TrivyPackage nodes with:
- is_direct property (direct vs transitive dependency)
- DEPENDS_ON relationships between packages

Package ID format matches Trivy's format: {version}|{name}
This enables the SBOM module to enrich TrivyPackage nodes created by the Trivy module.
"""

import logging
import re
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


def extract_image_digest(sbom_data: dict[str, Any]) -> str | None:
    """
    Extract the container image digest from the SBOM metadata.

    Handles multiple formats:
    - cdxgen/trivy: metadata.component.bom-ref or purl contains pkg:oci/repo@sha256:digest
    - Trivy properties: aquasecurity:trivy:RepoDigest or oci:image:RepoDigest
    - Component hashes: SHA-256 hash in metadata.component.hashes

    Args:
        sbom_data: CycloneDX SBOM data.

    Returns:
        The image digest string (sha256:...), or None if not found.
    """
    metadata = sbom_data.get("metadata", {})
    component = metadata.get("component", {})

    if component:
        # Method 1: Extract from bom-ref (cdxgen/trivy format)
        # Format: pkg:oci/repo@sha256:digest or pkg:oci/repo@sha256%3Adigest?qualifiers
        bom_ref = component.get("bom-ref", "")
        if "@sha256:" in bom_ref or "@sha256%3A" in bom_ref:
            decoded_ref = unquote(bom_ref)
            # Extract sha256:... from the bom-ref
            digest_part = decoded_ref.split("@")[-1]
            # Strip query parameters (e.g., ?arch=amd64&repository_url=...)
            if "?" in digest_part:
                digest_part = digest_part.split("?")[0]
            if digest_part.startswith("sha256:"):
                return digest_part

        # Method 2: Extract from purl (may be URL-encoded)
        # Format: pkg:oci/repo@sha256%3Adigest?qualifiers
        purl = component.get("purl", "")
        if purl:
            # Handle URL-encoded sha256
            decoded_purl = unquote(purl)
            if "@sha256:" in decoded_purl:
                digest_part = decoded_purl.split("@")[-1]
                # Strip query parameters (e.g., ?arch=amd64&repository_url=...)
                if "?" in digest_part:
                    digest_part = digest_part.split("?")[0]
                if digest_part.startswith("sha256:"):
                    return digest_part

        # Method 3: Check properties for image digest
        properties = component.get("properties", [])
        for prop in properties:
            prop_name = prop.get("name", "")
            if prop_name in (
                "aquasecurity:trivy:RepoDigest",
                "oci:image:RepoDigest",
                "RepoDigest",
            ):
                value = prop.get("value", "")
                if "@sha256:" in value:
                    return value.split("@")[-1]
                if value.startswith("sha256:"):
                    return value

        # Method 4: Check hashes
        hashes = component.get("hashes", [])
        for hash_entry in hashes:
            if hash_entry.get("alg") == "SHA-256":
                content = hash_entry.get("content", "")
                if content:
                    return f"sha256:{content}"

    # Method 5: Check for serialNumber which sometimes contains image info
    serial_number = sbom_data.get("serialNumber", "")
    if serial_number and "@sha256:" in serial_number:
        return serial_number.split("@")[-1]

    logger.warning("Could not extract image digest from SBOM metadata")
    return None


def get_direct_dependencies(sbom_data: dict[str, Any]) -> set[str]:
    """
    Determine which components are direct dependencies from the dependency graph.

    Direct dependencies are those that appear in the 'dependsOn' array of the
    root component (the first entry in the dependencies array typically
    represents the root/main component).

    Args:
        sbom_data: CycloneDX SBOM data.

    Returns:
        Set of bom-ref strings that are direct dependencies.
    """
    dependencies = sbom_data.get("dependencies", [])
    if not dependencies:
        # If no dependency graph, treat all components as direct
        components = sbom_data.get("components", [])
        return {comp.get("bom-ref", "") for comp in components if comp.get("bom-ref")}

    # Find the root component
    # The root is typically the metadata.component or the first dependency entry
    metadata = sbom_data.get("metadata", {})
    root_component = metadata.get("component", {})
    root_ref = root_component.get("bom-ref", "")

    # If we have a root ref, find its direct dependencies
    if root_ref:
        for dep in dependencies:
            if dep.get("ref") == root_ref:
                depends_on = dep.get("dependsOn", [])
                return set(depends_on)

    # Fallback: if first dependency entry has dependsOn, use those as direct
    if dependencies and dependencies[0].get("dependsOn"):
        return set(dependencies[0].get("dependsOn", []))

    # If no root found, treat all as direct
    components = sbom_data.get("components", [])
    return {comp.get("bom-ref", "") for comp in components if comp.get("bom-ref")}


def extract_ecosystem_from_purl(purl: str | None) -> str | None:
    """
    Extract the package ecosystem from a purl (Package URL).

    Args:
        purl: Package URL string (e.g., "pkg:npm/lodash@4.17.21").

    Returns:
        The ecosystem string (e.g., "npm", "pypi", "maven").
    """
    if not purl:
        return None

    # purl format: pkg:type/namespace/name@version?qualifiers#subpath
    # We want the 'type' which is the ecosystem
    match = re.match(r"^pkg:([^/]+)/", purl)
    if match:
        return match.group(1)

    return None


def transform_sbom_packages(
    sbom_data: dict[str, Any],
    image_digest: str,
) -> list[dict[str, Any]]:
    """
    Transform SBOM components into package data for enriching TrivyPackage nodes.

    Package IDs are generated in Trivy format: {version}|{name}
    This enables matching with existing TrivyPackage nodes created by the Trivy module.

    Args:
        sbom_data: CycloneDX SBOM data.
        image_digest: The image digest this SBOM belongs to (for reference).

    Returns:
        List of dictionaries containing package data with Trivy-compatible IDs.
    """
    components = sbom_data.get("components", [])
    direct_deps = get_direct_dependencies(sbom_data)

    packages = []
    for component in components:
        bom_ref = component.get("bom-ref", "")
        purl = component.get("purl")
        name = component.get("name", "")
        version = component.get("version", "")

        # Try to extract name and version from purl if not provided
        if purl and (not name or not version):
            extracted = extract_name_version_from_purl(purl)
            if extracted:
                name, version = extracted

        # Skip packages without name or version
        if not name or not version:
            logger.debug("Skipping component without name/version: %s", bom_ref)
            continue

        # Generate ID in Trivy format: {version}|{name}
        pkg_id = make_trivy_package_id(name, version)

        # Determine if this is a direct dependency
        is_direct = bom_ref in direct_deps if bom_ref else False

        # Extract ecosystem from purl or component type
        ecosystem = extract_ecosystem_from_purl(purl) or component.get("type", "")

        package_data = {
            "id": pkg_id,
            "purl": purl,
            "bom_ref": bom_ref,
            "name": name,
            "version": version,
            "ecosystem": ecosystem,
            "type": component.get("type", ""),
            "is_direct": is_direct,
            "image_digest": image_digest,
            # Fields for TrivyPackage compatibility
            "PkgName": name,
            "InstalledVersion": version,
        }
        packages.append(package_data)

    logger.debug(
        "Transformed %d packages from SBOM, %d direct dependencies",
        len(packages),
        sum(1 for p in packages if p["is_direct"]),
    )
    return packages


def transform_sbom_dependencies(
    sbom_data: dict[str, Any],
    image_digest: str,
) -> list[dict[str, Any]]:
    """
    Transform SBOM dependency graph into relationship data for MatchLinks.

    Creates data for DEPENDS_ON relationships between TrivyPackage nodes.
    Package IDs use Trivy format: {version}|{name}

    Args:
        sbom_data: CycloneDX SBOM data.
        image_digest: The image digest this SBOM belongs to (for reference).

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
