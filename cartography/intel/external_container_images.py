from collections.abc import Sequence
from typing import Any

import neo4j

from cartography.client.container_registry import ResolvedRegistryArtifact
from cartography.client.container_registry import ResolvedRegistryReference
from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.models.external_container_images import (
    ExternalContainerImageReferenceSchema,
)
from cartography.models.external_container_images import ExternalContainerImageSchema


def _artifact_row(
    artifact: ResolvedRegistryArtifact,
    child_image_digests: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "digest": artifact.digest,
        "type": artifact.type,
        "media_type": artifact.media_type,
        "size": artifact.size,
        "config_digest": artifact.config_digest,
        "created_at": artifact.created_at,
        "os": artifact.os,
        "architecture": artifact.architecture,
        "variant": artifact.variant,
        "child_image_digests": list(child_image_digests),
    }


def _digest_reference_row(
    resolved: ResolvedRegistryReference,
    artifact: ResolvedRegistryArtifact,
    *,
    is_top: bool,
) -> dict[str, Any]:
    reference = resolved.reference
    location = f"{reference.registry}/{reference.repository}@{artifact.digest}"
    return {
        "location": location,
        "original_reference": (
            reference.original
            if is_top and reference.digest and reference.normalized == location
            else location
        ),
        "registry": reference.registry,
        "repository": reference.repository,
        "tag": None,
        "digest": artifact.digest,
        "pullable_reference": location,
        "reference_type": "digest",
    }


def _exact_digest_reference_row(
    resolved: ResolvedRegistryReference,
) -> dict[str, Any] | None:
    reference = resolved.reference
    canonical_location = (
        f"{reference.registry}/{reference.repository}@{resolved.top.digest}"
    )
    if not reference.digest or reference.normalized == canonical_location:
        return None
    return {
        "location": reference.normalized,
        "original_reference": reference.original,
        "registry": reference.registry,
        "repository": reference.repository,
        "tag": reference.tag,
        "digest": resolved.top.digest,
        "pullable_reference": reference.normalized,
        "reference_type": "digest",
    }


def _tag_reference_row(resolved: ResolvedRegistryReference) -> dict[str, Any] | None:
    reference = resolved.reference
    if not reference.tag or reference.digest:
        return None
    return {
        "location": reference.normalized,
        "original_reference": reference.original,
        "registry": reference.registry,
        "repository": reference.repository,
        "tag": reference.tag,
        "digest": resolved.top.digest,
        "pullable_reference": (
            f"{reference.registry}/{reference.repository}@{resolved.top.digest}"
        ),
        "reference_type": "tag",
    }


def load_external_container_images(
    neo4j_session: neo4j.Session,
    resolved_references: Sequence[ResolvedRegistryReference],
    update_tag: int,
) -> None:
    """Load complete public-registry resolutions without broad cleanup.

    Failed resolutions never enter this function. Only successfully refreshed tag IDs
    can be rewired, so a partial sync cannot remove unrelated prior inventory.
    """
    if not resolved_references:
        return

    artifacts_by_digest: dict[str, dict[str, Any]] = {}
    references_by_location: dict[str, dict[str, Any]] = {}
    refreshed_tag_ids: set[str] = set()

    for resolved in resolved_references:
        child_digests = [child.digest for child in resolved.children]
        for child in resolved.children:
            artifacts_by_digest.setdefault(child.digest, _artifact_row(child))
        # Child targets must be loaded first even when load() splits a large closure
        # across batches.
        artifacts_by_digest[resolved.top.digest] = _artifact_row(
            resolved.top,
            child_digests,
        )

        for artifact in (resolved.top, *resolved.children):
            digest_reference = _digest_reference_row(
                resolved,
                artifact,
                is_top=artifact is resolved.top,
            )
            references_by_location[digest_reference["location"]] = digest_reference

        exact_digest_reference = _exact_digest_reference_row(resolved)
        if exact_digest_reference:
            references_by_location[exact_digest_reference["location"]] = (
                exact_digest_reference
            )

        tag_reference = _tag_reference_row(resolved)
        if tag_reference:
            references_by_location[tag_reference["location"]] = tag_reference
            refreshed_tag_ids.add(tag_reference["location"])

    load(
        neo4j_session,
        ExternalContainerImageSchema(),
        list(artifacts_by_digest.values()),
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        ExternalContainerImageReferenceSchema(),
        list(references_by_location.values()),
        lastupdated=update_tag,
    )

    # ponytail: immutable artifacts, digest references, and CONTAINS_IMAGE edges are
    # append-only; add orphan GC only when measured growth justifies ownership tracking.
    if refreshed_tag_ids:
        # A successful refresh may move a mutable tag.
        run_write_query(
            neo4j_session,
            """
            UNWIND $tag_reference_ids AS tag_reference_id
            MATCH (reference:ExternalContainerImageReference {id: tag_reference_id})
                  -[relationship:IMAGE]->(artifact:ExternalContainerImage)
            WHERE artifact.digest <> reference.digest
            DELETE relationship
            """,
            tag_reference_ids=sorted(refreshed_tag_ids),
        )
