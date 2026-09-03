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
            "metadata": {"manifestDigest": "sha256:...", "repoDigests": ["myimage@sha256:..."]}
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


def _append_digest(digests: list[str], digest: Any) -> None:
    if (
        isinstance(digest, str)
        and digest.startswith("sha256:")
        and digest not in digests
    ):
        digests.append(digest)


def _append_repo_digests(digests: list[str], repo_digests: Any) -> None:
    if not isinstance(repo_digests, list):
        return

    for repo_digest in repo_digests:
        if not isinstance(repo_digest, str):
            continue
        _, separator, digest = repo_digest.rpartition("@")
        if separator:
            _append_digest(digests, digest)


def _extract_image_digests(data: dict[str, Any]) -> list[str]:
    """
    Extract image digest candidates from Syft's current source metadata shape.

    The order is deterministic: manifestDigest first, then repoDigests.
    """
    source = data.get("source", {})
    if not isinstance(source, dict) or source.get("type") != "image":
        return []

    digests: list[str] = []

    metadata = source.get("metadata", {})
    if isinstance(metadata, dict):
        _append_digest(digests, metadata.get("manifestDigest"))
        _append_repo_digests(digests, metadata.get("repoDigests"))

    return digests


def _unique_extend(dest: list[str], values: list[str]) -> None:
    seen = set(dest)
    for value in values:
        if value not in seen:
            dest.append(value)
            seen.add(value)


def _artifact_found_by(artifact: dict[str, Any]) -> list[str]:
    found_by = artifact.get("foundBy")
    if isinstance(found_by, str) and found_by:
        return [found_by]
    return []


def _artifact_location_paths(artifact: dict[str, Any]) -> list[str]:
    locations = artifact.get("locations")
    if not isinstance(locations, list):
        return []

    paths: list[str] = []
    seen: set[str] = set()
    for location in locations:
        if not isinstance(location, dict):
            continue
        path = location.get("path")
        if isinstance(path, str) and path and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def transform_artifacts(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform Syft artifacts into SyftPackage node data with dependency_ids.

    Artifacts that share a normalized_id in one Syft document are merged into a
    single package row. Scan-local cataloger names and location paths are stored
    as lists for the DEPLOYED relationship to Image.

    The dependency_ids field lists the normalized_ids of packages this artifact
    depends on, derived from artifactRelationships.

    Args:
        data: Validated Syft JSON data

    Returns:
        List of dicts with keys: id, name, version, type, purl, normalized_id,
        language, found_by, locations, dependency_ids, ImageDigestCandidates
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

    image_digests = _extract_image_digests(data)
    source = data.get("source", {})
    if isinstance(source, dict) and source.get("type") == "image" and not image_digests:
        logger.warning(
            "Syft image source did not include image digest candidates; "
            "SyftPackage DEPLOYED relationships to Image nodes will be skipped.",
        )

    packages_by_id: dict[str, dict[str, Any]] = {}
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
        if not normalized_id:
            continue

        found_by = _artifact_found_by(artifact)
        locations = _artifact_location_paths(artifact)
        dependency_ids = dep_map.get(artifact_id, [])

        existing = packages_by_id.get(normalized_id)
        if existing is None:
            packages_by_id[normalized_id] = {
                "id": normalized_id,
                "name": name,
                "version": version,
                "type": artifact.get("type"),
                "purl": artifact.get("purl"),
                "normalized_id": normalized_id,
                "language": artifact.get("language"),
                "found_by": list(found_by),
                "locations": list(locations),
                "dependency_ids": list(dependency_ids),
                "ImageDigestCandidates": image_digests,
            }
            continue

        _unique_extend(existing["found_by"], found_by)
        _unique_extend(existing["locations"], locations)
        _unique_extend(existing["dependency_ids"], dependency_ids)

    return list(packages_by_id.values())
