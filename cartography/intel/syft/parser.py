"""
Parser module for Syft native JSON format.

This module provides functions to parse Syft's native JSON output and transform it
into DEPENDS_ON relationship data for enriching TrivyPackage nodes.

Syft JSON Format Reference:
    {
        "artifacts": [
            {"id": "abc123", "name": "express", "version": "4.18.2", "type": "npm", ...}
        ],
        "artifactRelationships": [
            {"parent": "abc123", "child": "def456", "type": "dependency-of"}
        ],
        "source": {
            "type": "image",
            "target": {"digest": "sha256:...", "tags": ["myimage:latest"]}
        },
        "schema": {"version": "16.0.0"}
    }

Syft Relationship Semantics:
    - "dependency-of": {parent: X, child: Y} means "Y depends on X" (Y requires X)
    - Example: {parent: "pydantic", child: "fastapi"} means fastapi depends on pydantic

Direct vs Transitive Dependencies:
    With the DEPENDS_ON graph, direct/transitive status is derivable:
    - Direct deps: packages with no incoming DEPENDS_ON edges (nothing depends on them)
    - Transitive deps: packages that have incoming DEPENDS_ON edges
"""

import logging
from typing import Any

from cartography.intel.trivy.util import make_normalized_package_id

logger = logging.getLogger(__name__)


class SyftValidationError(ValueError):
    """Raised when Syft JSON data fails validation."""

    pass


def validate_syft_json(data: dict[str, Any]) -> None:
    """
    Validate that the provided data is a valid Syft JSON structure.

    Args:
        data: Dictionary parsed from Syft JSON output

    Raises:
        SyftValidationError: If required fields are missing or invalid
    """
    if not isinstance(data, dict):
        raise SyftValidationError("Syft data must be a dictionary")

    if "artifacts" not in data:
        raise SyftValidationError("Syft data missing required 'artifacts' field")

    if not isinstance(data.get("artifacts", []), list):
        raise SyftValidationError("Syft 'artifacts' field must be a list")

    # artifactRelationships is optional but must be a list if present
    if "artifactRelationships" in data and not isinstance(
        data["artifactRelationships"], list
    ):
        raise SyftValidationError(
            "Syft 'artifactRelationships' field must be a list if present"
        )


def _build_artifact_lookup(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Build a lookup dictionary from Syft artifact ID to artifact data.

    Args:
        data: Syft JSON data

    Returns:
        Dictionary mapping artifact ID -> artifact data dict
    """
    return {artifact["id"]: artifact for artifact in data.get("artifacts", [])}


def transform_dependencies(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform Syft artifactRelationships into DEPENDS_ON relationship data.

    Creates relationship data for: (child)-[:DEPENDS_ON]->(parent)
    because in Syft's model, {parent: X, child: Y} means Y depends on X.

    Uses normalized_id for cross-tool matching to handle naming differences.

    Args:
        data: Validated Syft JSON data

    Returns:
        List of dicts with keys:
            - source_id: Normalized ID of the dependent (the one that needs)
            - target_id: Normalized ID of the dependency (the one that is needed)
    """
    artifacts = _build_artifact_lookup(data)
    relationships = data.get("artifactRelationships", [])
    dependency_data: list[dict[str, Any]] = []

    for rel in relationships:
        rel_type = rel.get("type", "")
        child_id = rel.get("child", "")
        parent_id = rel.get("parent", "")

        # Only process "dependency-of" relationships
        if rel_type != "dependency-of":
            continue

        # Both parent and child must be artifacts (packages)
        if parent_id not in artifacts or child_id not in artifacts:
            continue

        parent = artifacts[parent_id]
        child = artifacts[child_id]

        parent_name: str | None = parent.get("name")
        parent_version: str | None = parent.get("version")
        child_name: str | None = child.get("name")
        child_version: str | None = child.get("version")

        # Skip if any required fields are missing
        if not parent_name or not parent_version or not child_name or not child_version:
            logger.debug(
                "Skipping relationship %s -> %s: missing name or version",
                parent_id,
                child_id,
            )
            continue

        # Compute normalized IDs for cross-tool matching
        parent_norm_id = make_normalized_package_id(
            purl=parent.get("purl"),
            name=parent_name,
            version=parent_version,
            pkg_type=parent.get("type"),
        )
        child_norm_id = make_normalized_package_id(
            purl=child.get("purl"),
            name=child_name,
            version=child_version,
            pkg_type=child.get("type"),
        )

        # Skip if normalization failed
        if not parent_norm_id or not child_norm_id:
            logger.debug(
                "Skipping relationship %s -> %s: normalization failed",
                parent_id,
                child_id,
            )
            continue

        # DEPENDS_ON: child depends on parent (child needs parent)
        # So: (child)-[:DEPENDS_ON]->(parent)
        dependency_data.append(
            {
                "source_id": child_norm_id,
                "target_id": parent_norm_id,
            }
        )

    return dependency_data


def get_image_digest_from_syft(data: dict[str, Any]) -> str | None:
    """
    Extract the image digest from Syft JSON source metadata.

    Args:
        data: Syft JSON data

    Returns:
        Image digest string (e.g., "sha256:abc123...") or None if not found
    """
    source = data.get("source", {})

    # For image sources, digest is in target
    target = source.get("target", {})
    if isinstance(target, dict):
        digest = target.get("digest")
        if digest:
            return digest

        # Also check for repoDigests
        repo_digests = target.get("repoDigests", [])
        if repo_digests and len(repo_digests) > 0:
            # Extract digest from repo digest format: "repo@sha256:..."
            first_digest = repo_digests[0]
            if "@" in first_digest:
                return first_digest.split("@")[1]

    return None
