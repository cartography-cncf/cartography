import asyncio
import json
import logging
from typing import Any

import httpx
import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.manifest import build_blob_url
from cartography.intel.gcp.artifact_registry.manifest import build_manifest_url
from cartography.intel.gcp.artifact_registry.manifest import parse_docker_image_uri
from cartography.intel.gcp.clients import _resolve_credentials
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.intel.supply_chain import extract_layers_from_oci_config
from cartography.intel.supply_chain import extract_provenance_from_oci_config
from cartography.intel.supply_chain import unwrap_attestation_predicate
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryContainerImageProvenanceSchema,
)
from cartography.models.gcp.artifact_registry.image_layer import (
    GCPArtifactRegistryImageLayerSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

SINGLE_IMAGE_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
}

ALL_MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)

ATTESTATION_MEDIA_TYPE_FRAGMENTS = {"attestation", "in-toto"}


async def _fetch_json(
    http_client: httpx.AsyncClient,
    url: str,
    auth_token: str,
    accept: str | None = None,
) -> dict[str, Any] | None:
    headers: dict[str, str] = {"Authorization": f"Bearer {auth_token}"}
    if accept:
        headers["Accept"] = accept
    try:
        resp = await http_client.get(url, headers=headers, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return None


async def _fetch_manifest_with_digest(
    http_client: httpx.AsyncClient,
    url: str,
    auth_token: str,
    accept: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch a manifest and return (manifest_json, subject_digest)."""
    headers = {"Authorization": f"Bearer {auth_token}", "Accept": accept}
    try:
        resp = await http_client.get(url, headers=headers, timeout=30.0)
        resp.raise_for_status()
        digest = resp.headers.get("Docker-Content-Digest")
        return resp.json(), digest
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return None, None


async def _fetch_image_config(
    http_client: httpx.AsyncClient,
    auth_token: str,
    registry: str,
    image_path: str,
    reference: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch OCI image config and return (config, manifest_digest)."""
    manifest_url = build_manifest_url(registry, image_path, reference)
    manifest, manifest_digest = await _fetch_manifest_with_digest(
        http_client,
        manifest_url,
        auth_token,
        ALL_MANIFEST_ACCEPT,
    )
    if not manifest:
        return None, None

    config_descriptor = manifest.get("config", {})
    config_digest = config_descriptor.get("digest")
    config_media_type = config_descriptor.get("mediaType", "")

    if not config_digest:
        return None, None
    if any(
        frag in config_media_type.lower() for frag in ATTESTATION_MEDIA_TYPE_FRAGMENTS
    ):
        return None, None

    blob_url = build_blob_url(registry, image_path, config_digest)
    config = await _fetch_json(http_client, blob_url, auth_token)
    return config, manifest_digest


async def _fetch_attestation_provenance(
    http_client: httpx.AsyncClient,
    auth_token: str,
    registry: str,
    image_path: str,
    image_digest: str,
) -> dict[str, str]:
    """Attempt to find SLSA provenance via the OCI Referrers API."""
    referrers_url = f"https://{registry}/v2/{image_path}/referrers/{image_digest}"
    index = await _fetch_json(http_client, referrers_url, auth_token)
    if not index:
        return {}

    for ref_manifest in index.get("manifests", []):
        artifact_type = ref_manifest.get("artifactType", "")
        if (
            "provenance" not in artifact_type.lower()
            and "slsa" not in artifact_type.lower()
        ):
            continue

        ref_digest = ref_manifest.get("digest")
        if not ref_digest:
            continue

        att_manifest_url = build_manifest_url(registry, image_path, ref_digest)
        att_manifest = await _fetch_json(http_client, att_manifest_url, auth_token)
        if not att_manifest:
            continue

        for layer in att_manifest.get("layers", []):
            layer_mt = layer.get("mediaType", "").lower()
            if "in-toto" not in layer_mt and "provenance" not in layer_mt:
                continue

            layer_digest = layer.get("digest")
            if not layer_digest:
                continue

            blob_url = build_blob_url(registry, image_path, layer_digest)
            blob = await _fetch_json(http_client, blob_url, auth_token)
            if not blob:
                continue

            predicate = blob.get("predicate", {})
            predicate = unwrap_attestation_predicate(predicate) or predicate
            provenance = extract_image_source_provenance(predicate)
            if provenance:
                return provenance

    return {}


async def _process_single_image(
    http_client: httpx.AsyncClient,
    auth_token: str,
    artifact: dict[str, Any],
) -> dict[str, Any] | None:
    """Process one image: fetch config, extract provenance + layers."""
    name = artifact.get("name", "")
    uri = artifact.get("uri", "")

    parsed = parse_docker_image_uri(uri)
    if not parsed:
        return None

    registry, image_path, reference = parsed

    config, manifest_digest = await _fetch_image_config(
        http_client, auth_token, registry, image_path, reference
    )
    if not config:
        return None

    provenance = extract_provenance_from_oci_config(config)

    # OCI labels are fast but not always present; fall back to the Referrers API.
    # The Referrers endpoint requires a digest, not a tag.
    if not provenance.get("source_uri"):
        subject_digest = uri.split("@")[-1] if "@" in uri else manifest_digest
        if subject_digest and subject_digest.startswith("sha256:"):
            slsa_provenance = await _fetch_attestation_provenance(
                http_client,
                auth_token,
                registry,
                image_path,
                subject_digest,
            )
            provenance.update(slsa_provenance)

    diff_ids, layer_history = extract_layers_from_oci_config(config)

    if not provenance.get("source_uri") and not diff_ids:
        return None

    result: dict[str, Any] = {
        "id": name,
    }
    if provenance.get("source_uri"):
        result["source_uri"] = provenance["source_uri"]
    if provenance.get("source_revision"):
        result["source_revision"] = provenance["source_revision"]
    if provenance.get("source_file"):
        result["source_file"] = provenance["source_file"]
    if diff_ids:
        result["layer_diff_ids"] = diff_ids
        result["layer_history"] = layer_history

    return result


async def _fetch_all_image_provenance(
    credentials: GoogleCredentials | None,
    docker_artifacts_raw: list[dict[str, Any]],
    project_id: str,
    max_concurrent: int = 50,
) -> list[dict[str, Any]]:
    resolved = _resolve_credentials(credentials)
    if not resolved.valid:
        resolved.refresh(Request())
    auth_token = resolved.token

    single_images = [
        a
        for a in docker_artifacts_raw
        if a.get("mediaType", "") in SINGLE_IMAGE_MEDIA_TYPES
    ]
    if not single_images:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[dict[str, Any]] = []

    async def bounded_process(
        artifact: dict[str, Any], client: httpx.AsyncClient
    ) -> dict[str, Any] | None:
        async with semaphore:
            return await _process_single_image(client, auth_token, artifact)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [asyncio.create_task(bounded_process(a, client)) for a in single_images]
        total = len(tasks)

        logger.info("Fetching OCI configs for %d single-image artifacts...", total)
        progress_interval = max(1, min(100, total // 10 or 1))
        completed = 0

        for task in asyncio.as_completed(tasks):
            result = await task
            completed += 1
            if completed % progress_interval == 0 or completed == total:
                logger.info(
                    "Processed %d/%d images (%.1f%%)",
                    completed,
                    total,
                    (completed / total) * 100,
                )
            if result is not None:
                results.append(result)

    logger.info(
        "Extracted provenance/layer data for %d of %d images",
        len(results),
        total,
    )
    return results


def _build_layer_dicts(
    enrichments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate and build ImageLayer node dicts from enrichment results.

    Creates a node for every diff_id. History commands are matched to
    diff_ids by skipping empty-layer entries (which have no diff_id),
    but layers are still created even when history is absent or truncated.
    """
    layers_by_diff_id: dict[str, dict[str, Any]] = {}

    for enrichment in enrichments:
        diff_ids = enrichment.get("layer_diff_ids", [])
        history_entries = enrichment.get("layer_history", [])

        # Map diff_id index → history command by skipping empty layers
        history_by_idx: dict[int, str | None] = {}
        non_empty_idx = 0
        for entry in history_entries:
            if entry.get("empty_layer", False):
                continue
            history_by_idx[non_empty_idx] = entry.get("created_by") or None
            non_empty_idx += 1

        for idx, diff_id in enumerate(diff_ids):
            if diff_id not in layers_by_diff_id:
                layers_by_diff_id[diff_id] = {
                    "diff_id": diff_id,
                    "is_empty": False,
                    "history": history_by_idx.get(idx),
                }

    return list(layers_by_diff_id.values())


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: GoogleCredentials | None,
    docker_artifacts_raw: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Enrich GCP Artifact Registry container images with build provenance and layer data.

    Fetches OCI image configs from the Docker Registry API, extracts provenance
    metadata (source_uri, source_revision) and layer information, then updates
    the image nodes in the graph. This enables the existing GitHub/GitLab supply
    chain modules to create PACKAGED_FROM relationships via provenance matching
    and Dockerfile analysis.
    """
    logger.info("Starting supply chain sync for GCP project %s", project_id)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    enrichments = loop.run_until_complete(
        _fetch_all_image_provenance(credentials, docker_artifacts_raw, project_id),
    )

    if not enrichments:
        logger.info("No provenance or layer data found for project %s", project_id)
        return

    # Update image nodes with provenance fields
    provenance_updates = [
        {
            "id": e["id"],
            "source_uri": e.get("source_uri"),
            "source_revision": e.get("source_revision"),
            "source_file": e.get("source_file"),
            "layer_diff_ids": e.get("layer_diff_ids"),
        }
        for e in enrichments
    ]
    load(
        neo4j_session,
        GCPArtifactRegistryContainerImageProvenanceSchema(),
        provenance_updates,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )

    # Create ImageLayer nodes
    layer_dicts = _build_layer_dicts(enrichments)
    if layer_dicts:
        logger.info("Loading %d image layer nodes", len(layer_dicts))
        load(
            neo4j_session,
            GCPArtifactRegistryImageLayerSchema(),
            layer_dicts,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )

    # Cleanup stale layers
    cleanup_params = common_job_parameters.copy()
    cleanup_params["PROJECT_ID"] = project_id
    GraphJob.from_node_schema(
        GCPArtifactRegistryImageLayerSchema(),
        cleanup_params,
    ).run(neo4j_session)

    provenance_count = sum(1 for e in enrichments if e.get("source_uri"))
    layer_count = sum(1 for e in enrichments if e.get("layer_diff_ids"))
    logger.info(
        "Completed supply chain sync for GCP project %s: "
        "%d images with provenance, %d with layer data, %d unique layers",
        project_id,
        provenance_count,
        layer_count,
        len(layer_dicts),
    )
