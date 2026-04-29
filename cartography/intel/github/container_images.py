"""
GitHub Container Images Intelligence Module.

For each container package owned by an organization, fetches the OCI manifests
(and child manifests for multi-arch images) from ghcr.io, plus the referenced
image config blobs to extract layer diff IDs and platform metadata.

Within-run de-duplication keeps ``(digest -> manifest)`` and
``(config_digest -> config)`` maps so a config that is referenced by 50 tags
is fetched once. Cross-run de-duplication checks the graph for digests that
already have ``layer_diff_ids`` set and skips the manifest+config fetches —
the previous sync already populated those properties.
"""

import logging
from typing import Any
from typing import cast

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.intel.github.packages import get_package_versions
from cartography.intel.github.util import fetch_ghcr_blob
from cartography.intel.github.util import fetch_ghcr_manifest
from cartography.models.github.container_image_layers import (
    GitHubContainerImageLayerSchema,
)
from cartography.models.github.container_images import GitHubContainerImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


CONTAINER_IMAGE_BATCH_SIZE = 500
CONTAINER_IMAGE_LAYER_BATCH_SIZE = 200

MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def _ghcr_repository_name(org_login: str, package_name: str) -> str:
    return f"{org_login.lower()}/{package_name.lower()}"


def _existing_digests_with_layers(
    neo4j_session: neo4j.Session,
    org_url: str,
) -> set[str]:
    """
    Return the set of GHCR image digests that already have ``layer_diff_ids``
    populated in the graph. We use this to skip manifest/config fetches for
    images we've fully ingested in a previous run — the steady-state cost
    drops from O(versions) to O(new versions).
    """
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})
    MATCH (org)-[:RESOURCE]->(img:GitHubContainerImage)
    WHERE img.layer_diff_ids IS NOT NULL AND size(img.layer_diff_ids) > 0
    RETURN img.digest
    """
    values = neo4j_session.execute_read(
        read_list_of_values_tx,
        query,
        org_url=org_url,
    )
    return {v for v in cast(list[str], values) if v}


def _process_manifest(
    token: Any,
    repository_name: str,
    digest: str,
    package_id: str,
    package_uri: str,
    config_cache: dict[str, dict[str, Any] | None],
    seen_digests: set[str],
    out_manifests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Fetch a single manifest, attach the resolved config blob, and append to
    ``out_manifests``. Returns the manifest (or None if missing). Handles
    in-run dedup via ``seen_digests``.
    """
    if digest in seen_digests:
        return None
    seen_digests.add(digest)

    manifest = fetch_ghcr_manifest(token, repository_name, digest)
    if manifest is None:
        logger.debug(
            "GHCR manifest %s for %s not found; skipping",
            digest,
            repository_name,
        )
        return None

    manifest["_digest"] = digest
    manifest["_repository_name"] = repository_name
    manifest["_package_id"] = package_id
    manifest["_package_uri"] = package_uri

    media_type = manifest.get("mediaType")
    if media_type not in MANIFEST_LIST_MEDIA_TYPES:
        config_ref = manifest.get("config") or {}
        config_digest = config_ref.get("digest")
        if config_digest:
            if config_digest not in config_cache:
                # fetch_ghcr_blob returns None on 404 and raises on every other
                # HTTP error, so the sync fails loudly on auth/5xx and only the
                # legitimate "blob missing" case yields None here.
                config_cache[config_digest] = fetch_ghcr_blob(
                    token,
                    repository_name,
                    config_digest,
                )
                if config_cache[config_digest] is None:
                    logger.warning(
                        "GHCR config blob %s missing for %s (404); image "
                        "will be ingested without layer/arch metadata.",
                        config_digest,
                        repository_name,
                    )
            config_blob = config_cache[config_digest]
            if config_blob is not None:
                manifest["_config"] = config_blob
        else:
            manifest["_config"] = {}

    out_manifests.append(manifest)
    return manifest


@timeit
def get_container_images(
    token: Any,
    api_url: str,
    organization: str,
    packages: list[dict[str, Any]],
    skip_digests: set[str] | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    set[str],
]:
    """
    Fetch every image manifest reachable from the org's container packages.

    :returns: ``(all_manifests, manifest_lists, tag_rows, observed_and_skipped)``
        — ``all_manifests`` is the list of single-image manifests AND manifest
        lists (so each becomes a node); ``manifest_lists`` is the subset that
        are multi-arch indexes (used by the attestations sync); ``tag_rows``
        is the list of ``GitHubContainerImageTag`` rows ready for ingestion;
        ``observed_and_skipped`` is the set of digests that were present in
        the versions API but skipped by the cross-run dedup so the caller can
        refresh their ``lastupdated`` and avoid having cleanup reap them.
    """
    skip_digests = skip_digests or set()
    all_manifests: list[dict[str, Any]] = []
    manifest_lists: list[dict[str, Any]] = []
    tag_rows: list[dict[str, Any]] = []
    config_cache: dict[str, dict[str, Any] | None] = {}
    observed_and_skipped: set[str] = set()

    for pkg in packages:
        package_name = pkg["name"]
        package_id = pkg["html_url"]
        package_uri = pkg["uri"]
        repository_name = _ghcr_repository_name(organization, package_name)
        seen_digests: set[str] = set()

        versions = get_package_versions(token, api_url, organization, package_name)
        for version in versions:
            digest = version.get("name")
            if not digest or not digest.startswith("sha256:"):
                continue
            tag_names = (
                version.get("metadata", {}).get("container", {}).get("tags") or []
            )
            updated_at = version.get("updated_at")
            for tag_name in tag_names:
                tag_rows.append(
                    {
                        "name": tag_name,
                        "uri": f"{package_uri}:{tag_name}",
                        "digest": digest,
                        "image_pushed_at": updated_at,
                        "package_id": package_id,
                    },
                )

            # Cross-run dedup: skip manifest/config fetches for digests we've
            # already enriched. Tag rows are still produced above. The caller
            # bumps `lastupdated` on these digests so cleanup leaves them
            # alone — without that bump the optimization causes data loss.
            if digest in skip_digests:
                observed_and_skipped.add(digest)
                continue

            manifest = _process_manifest(
                token,
                repository_name,
                digest,
                package_id,
                package_uri,
                config_cache,
                seen_digests,
                all_manifests,
            )
            if manifest is None:
                continue

            media_type = manifest.get("mediaType")
            if media_type in MANIFEST_LIST_MEDIA_TYPES:
                manifest_lists.append(manifest)
                for child in manifest.get("manifests", []) or []:
                    annotations = child.get("annotations") or {}
                    if (
                        annotations.get("vnd.docker.reference.type")
                        == "attestation-manifest"
                    ):
                        continue
                    child_digest = child.get("digest")
                    if not child_digest:
                        continue
                    if child_digest in skip_digests:
                        observed_and_skipped.add(child_digest)
                        continue
                    _process_manifest(
                        token,
                        repository_name,
                        child_digest,
                        package_id,
                        package_uri,
                        config_cache,
                        seen_digests,
                        all_manifests,
                    )

    logger.info(
        "Fetched %d unique GHCR manifests (%d manifest lists, %d tags) across %d packages",
        len(all_manifests),
        len(manifest_lists),
        len(tag_rows),
        len(packages),
    )
    return all_manifests, manifest_lists, tag_rows, observed_and_skipped


def transform_container_images(
    raw_manifests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Shape OCI manifests for ``GitHubContainerImageSchema``."""
    transformed: list[dict[str, Any]] = []
    for manifest in raw_manifests:
        media_type = manifest.get("mediaType")
        is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES

        child_image_digests: list[str] | None = None
        if is_manifest_list:
            children = manifest.get("manifests") or []
            child_image_digests = [
                c.get("digest")
                for c in children
                if c.get("digest")
                and (c.get("annotations") or {}).get("vnd.docker.reference.type")
                != "attestation-manifest"
            ]

        config = manifest.get("_config") or {}

        layer_diff_ids: list[str] | None = None
        head_layer_diff_id: str | None = None
        tail_layer_diff_id: str | None = None
        if not is_manifest_list:
            diff_ids = (config.get("rootfs") or {}).get("diff_ids")
            if isinstance(diff_ids, list) and diff_ids:
                layer_diff_ids = diff_ids
                head_layer_diff_id = diff_ids[0]
                tail_layer_diff_id = diff_ids[-1]

        package_uri = manifest.get("_package_uri")
        digest = manifest.get("_digest")
        uri = f"{package_uri}@{digest}" if package_uri and digest else None

        transformed.append(
            {
                "digest": digest,
                "uri": uri,
                "media_type": media_type,
                "schema_version": manifest.get("schemaVersion"),
                "type": "manifest_list" if is_manifest_list else "image",
                "architecture": config.get("architecture"),
                "os": config.get("os"),
                "variant": config.get("variant"),
                "child_image_digests": child_image_digests,
                "layer_diff_ids": layer_diff_ids,
                "head_layer_diff_id": head_layer_diff_id,
                "tail_layer_diff_id": tail_layer_diff_id,
                "package_id": manifest.get("_package_id"),
            },
        )
    return transformed


def transform_container_image_layers(
    raw_manifests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build layer rows keyed by ``diff_id``. NEXT relationships chain layers in
    config order so the linked-list traversal matches the ECR/GitLab pattern.
    """
    layers_by_diff_id: dict[str, dict[str, Any]] = {}
    skipped = 0

    for manifest in raw_manifests:
        if manifest.get("mediaType") in MANIFEST_LIST_MEDIA_TYPES:
            continue

        layers = manifest.get("layers") or []
        config = manifest.get("_config") or {}
        rootfs = config.get("rootfs") or {}
        diff_ids = rootfs.get("diff_ids") or []
        history = config.get("history") or []

        # Align history entries to diff_ids — empty layers don't consume diff_ids.
        history_by_diff_id: dict[str, str] = {}
        idx = 0
        for entry in history:
            if not isinstance(entry, dict) or entry.get("empty_layer"):
                continue
            if idx >= len(diff_ids):
                break
            created_by = entry.get("created_by")
            if created_by:
                history_by_diff_id[str(diff_ids[idx])] = str(created_by)
            idx += 1

        for i, layer in enumerate(layers):
            layer_digest = layer.get("digest")
            diff_id = diff_ids[i] if i < len(diff_ids) else None
            if not layer_digest or not diff_id:
                skipped += 1
                continue

            entry = layers_by_diff_id.setdefault(
                diff_id,
                {
                    "diff_id": diff_id,
                    "digest": layer_digest,
                    "media_type": layer.get("mediaType"),
                    "size": layer.get("size"),
                    "is_empty": False,
                    "history": history_by_diff_id.get(str(diff_id)),
                    "next_diff_ids": set(),
                },
            )
            if i < len(layers) - 1:
                next_diff_id = diff_ids[i + 1] if i + 1 < len(diff_ids) else None
                if next_diff_id:
                    entry["next_diff_ids"].add(next_diff_id)

    out: list[dict[str, Any]] = []
    for layer in layers_by_diff_id.values():
        row: dict[str, Any] = {
            "diff_id": layer["diff_id"],
            "digest": layer["digest"],
            "media_type": layer["media_type"],
            "size": layer["size"],
            "is_empty": layer["is_empty"],
        }
        if layer["history"]:
            row["history"] = layer["history"]
        if layer["next_diff_ids"]:
            row["next_diff_ids"] = list(layer["next_diff_ids"])
        out.append(row)

    if skipped:
        logger.warning(
            "Skipped %d GHCR layer(s) due to missing digest or diff_id",
            skipped,
        )
    return out


@timeit
def load_container_images(
    neo4j_session: neo4j.Session,
    images: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubContainerImageSchema(),
        images,
        batch_size=CONTAINER_IMAGE_BATCH_SIZE,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_container_image_layers(
    neo4j_session: neo4j.Session,
    layers: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubContainerImageLayerSchema(),
        layers,
        batch_size=CONTAINER_IMAGE_LAYER_BATCH_SIZE,
        lastupdated=update_tag,
        org_url=org_url,
    )


def _refresh_skipped_image_lastupdated(
    neo4j_session: neo4j.Session,
    digests: set[str],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Bump ``lastupdated`` on container images (and their layer/relationship
    metadata) that were observed in the GHCR versions API this run but had
    their manifest+config fetch short-circuited by the cross-run dedup.

    Without this, the cleanup job — which deletes nodes / rels whose
    ``lastupdated`` doesn't match the current ``update_tag`` — would reap
    the live image, the per-layer rels (HAS_LAYER / HEAD / TAIL) and the
    layer-chain ``NEXT`` rels that order the linked list.
    """
    if not digests:
        return

    # First pass: refresh image node, RESOURCE rels and image->layer rels.
    image_layer_query = """
    MATCH (org:GitHubOrganization {id: $org_url})-[r_org:RESOURCE]->(img:GitHubContainerImage)
    WHERE img.digest IN $digests
    SET img.lastupdated = $update_tag,
        r_org.lastupdated = $update_tag
    WITH org, img
    OPTIONAL MATCH (img)-[r_layer:HAS_LAYER|HEAD|TAIL]->(layer:GitHubContainerImageLayer)
    SET r_layer.lastupdated = $update_tag,
        layer.lastupdated = $update_tag
    WITH org, layer
    WHERE layer IS NOT NULL
    OPTIONAL MATCH (org)-[r_layer_org:RESOURCE]->(layer)
    SET r_layer_org.lastupdated = $update_tag
    """
    neo4j_session.run(
        image_layer_query,
        digests=list(digests),
        org_url=org_url,
        update_tag=update_tag,
    )

    # Second pass: refresh the NEXT rels that chain the layers of any
    # refreshed image. Scoped to the current org because image digests are
    # content hashes — without that constraint a digest collision across
    # orgs would update unrelated images' NEXT chains.
    next_rel_query = """
    MATCH (org:GitHubOrganization {id: $org_url})-[:RESOURCE]->(img:GitHubContainerImage)
    WHERE img.digest IN $digests
    MATCH (img)-[:HAS_LAYER]->(l1:GitHubContainerImageLayer)
    MATCH (l1)-[r_next:NEXT]->(l2:GitHubContainerImageLayer)
    WHERE (img)-[:HAS_LAYER]->(l2)
    SET r_next.lastupdated = $update_tag
    """
    neo4j_session.run(
        next_rel_query,
        digests=list(digests),
        org_url=org_url,
        update_tag=update_tag,
    )


@timeit
def cleanup_container_images(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        GitHubContainerImageSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_container_image_layers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        GitHubContainerImageLayerSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_images(
    neo4j_session: neo4j.Session,
    token: Any,
    api_url: str,
    organization: str,
    packages: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    set[str],
]:
    """Returns ``(raw_manifests, manifest_lists, tag_rows, observed_and_skipped)``."""
    org_url = f"https://github.com/{organization}"
    skip_digests = _existing_digests_with_layers(neo4j_session, org_url)
    if skip_digests:
        logger.info(
            "Skipping manifest/config fetches for %d already-enriched GHCR digests",
            len(skip_digests),
        )

    (
        raw_manifests,
        manifest_lists,
        tag_rows,
        observed_and_skipped,
    ) = get_container_images(
        token,
        api_url,
        organization,
        packages,
        skip_digests=skip_digests,
    )
    images = transform_container_images(raw_manifests)
    layers = transform_container_image_layers(raw_manifests)

    if layers:
        load_container_image_layers(neo4j_session, layers, org_url, update_tag)
    if images:
        load_container_images(neo4j_session, images, org_url, update_tag)

    # Refresh lastupdated for digests we observed in versions but whose
    # manifest/config fetch we skipped via cross-run dedup. Must happen
    # before cleanup, otherwise the still-live images get reaped.
    _refresh_skipped_image_lastupdated(
        neo4j_session,
        observed_and_skipped,
        org_url,
        update_tag,
    )

    cleanup_params = dict(common_job_parameters)
    cleanup_params["org_url"] = org_url
    cleanup_container_image_layers(neo4j_session, cleanup_params)
    cleanup_container_images(neo4j_session, cleanup_params)
    return raw_manifests, manifest_lists, tag_rows, observed_and_skipped
