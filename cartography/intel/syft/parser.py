"""
Parser module for Syft native JSON format.

This module provides functions to parse Syft's native JSON output and transform
artifacts into SyftPackage node data with dependency relationships.

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


def _build_artifact_lookup(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Build a lookup dictionary from Syft artifact ID to artifact data.

    Args:
        data: Syft JSON data

    Returns:
        Dictionary mapping artifact ID -> artifact data dict
    """
    return {artifact["id"]: artifact for artifact in data.get("artifacts", [])}


def transform_artifacts(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform Syft artifacts into SyftPackage node data with dependency_ids.

    Each artifact becomes a SyftPackage node. The dependency_ids field lists
    the normalized_ids of packages this artifact depends on, derived from
    artifactRelationships.

    Args:
        data: Validated Syft JSON data

    Returns:
        List of dicts with keys: id, name, version, type, purl, normalized_id,
        language, found_by, dependency_ids
    """
    artifacts = _build_artifact_lookup(data)
    relationships = data.get("artifactRelationships", [])

    # Build child -> list of parent normalized_ids (child depends on parents)
    dep_map: dict[str, list[str]] = {}
    for rel in relationships:
        if rel.get("type") != "dependency-of":
            continue
        child_id = rel.get("child", "")
        parent_id = rel.get("parent", "")
        if child_id not in artifacts or parent_id not in artifacts:
            continue

        parent = artifacts[parent_id]
        parent_name = parent.get("name")
        parent_version = parent.get("version")
        if not parent_name or not parent_version:
            continue

        parent_norm_id = make_normalized_package_id(
            purl=parent.get("purl"),
            name=parent_name,
            version=parent_version,
            pkg_type=parent.get("type"),
        )
        if not parent_norm_id:
            continue
        dep_map.setdefault(child_id, []).append(parent_norm_id)

    packages: list[dict[str, Any]] = []
    for artifact_id, artifact in artifacts.items():
        name = artifact.get("name")
        version = artifact.get("version")
        if not name or not version:
            logger.debug("Skipping artifact %s: missing name or version", artifact_id)
            continue

        normalized_id = make_normalized_package_id(
            purl=artifact.get("purl"),
            name=name,
            version=version,
            pkg_type=artifact.get("type"),
        )
        packages.append(
            {
                "id": normalized_id,
                "name": name,
                "version": version,
                "type": artifact.get("type"),
                "purl": artifact.get("purl"),
                "normalized_id": normalized_id,
                "language": artifact.get("language"),
                "found_by": artifact.get("foundBy"),
                "dependency_ids": dep_map.get(artifact_id, []),
            }
        )

    return packages
