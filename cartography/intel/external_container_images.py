import logging
from collections.abc import Sequence
from typing import Any

import neo4j

from cartography.client.container_registry import ResolvedRegistryArtifact
from cartography.client.container_registry import ResolvedRegistryReference
from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import run_write_query
from cartography.models.external_container_images import (
    ExternalContainerImageReferenceSchema,
)
from cartography.models.external_container_images import ExternalContainerImageSchema

logger = logging.getLogger(__name__)


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


def _record_artifact(
    artifacts_by_digest: dict[str, dict[str, Any]],
    artifact: ResolvedRegistryArtifact,
    child_image_digests: Sequence[str] = (),
) -> None:
    row = _artifact_row(artifact, child_image_digests)
    existing = artifacts_by_digest.get(artifact.digest)
    if existing is None:
        artifacts_by_digest[artifact.digest] = row
        return
    _merge_artifact_rows(existing, row)


def _merge_artifact_rows(
    target: dict[str, Any],
    source: dict[str, Any],
    *,
    prefer_source: bool = False,
) -> None:
    for field, current in target.items():
        value = source.get(field)
        if current is None:
            target[field] = value
        elif value is not None and current != value:
            logger.warning(
                "Keeping previously observed %s for external image digest %s",
                field,
                target["digest"],
            )
            if prefer_source:
                target[field] = value


def _merge_existing_artifact_metadata(
    neo4j_session: neo4j.Session,
    artifacts_by_digest: dict[str, dict[str, Any]],
) -> None:
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        """
        UNWIND $digests AS digest
        MATCH (artifact:ExternalContainerImage {digest: digest})
        RETURN properties(artifact) AS artifact
        """,
        digests=list(artifacts_by_digest),
    )
    for row in rows:
        existing = row["artifact"]
        _merge_artifact_rows(
            artifacts_by_digest[existing["digest"]],
            existing,
            prefer_source=True,
        )


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
            else None
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
            _record_artifact(artifacts_by_digest, child)
        # Child targets must be loaded first even when load() splits a large closure
        # across batches.
        _record_artifact(
            artifacts_by_digest,
            resolved.top,
            child_digests,
        )

        for index, artifact in enumerate((resolved.top, *resolved.children)):
            digest_reference = _digest_reference_row(
                resolved,
                artifact,
                is_top=index == 0,
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

    _merge_existing_artifact_metadata(neo4j_session, artifacts_by_digest)
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
