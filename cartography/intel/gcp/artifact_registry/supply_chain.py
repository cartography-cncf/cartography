import asyncio
import json
import logging
from typing import Any

import httpx
import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request

from cartography.graph.job import GraphJob
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.gcp.artifact_registry.manifest import build_blob_url
from cartography.intel.gcp.artifact_registry.manifest import build_manifest_url
from cartography.intel.gcp.artifact_registry.manifest import parse_docker_image_uri
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import load_matchlinks_with_progress
from cartography.intel.gcp.artifact_registry.util import (
    load_nodes_without_relationships,
)
from cartography.intel.gcp.clients import _resolve_credentials
from cartography.intel.supply_chain import decode_attestation_blob_to_predicate
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.intel.supply_chain import extract_layers_from_oci_config
from cartography.intel.supply_chain import extract_provenance_from_oci_config
from cartography.models.gcp.artifact_registry.container_image import (
    GCPArtifactRegistryContainerImageProvenanceSchema,
)
from cartography.models.gcp.artifact_registry.image_layer import (
    GCPArtifactRegistryImageLayerSchema,
)
from cartography.models.gcp.artifact_registry.image_layer import (
    GCPArtifactRegistryProjectToImageLayerRel,
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


class _TokenManager:
    """Holds GCP credentials and exposes auth that can be refreshed on 401.

    The Docker Registry API rejects expired bearer tokens with a 401, which can
    happen mid-run on long enrichment passes against large registries. The
    manager refreshes the underlying credentials at most once per generation:
    concurrent 401s observe the same generation and only one task triggers the
    refresh, the others retry with the freshly minted token.

    Auth headers are applied via google-auth's ``credentials.apply`` so we keep
    parity with the official client behavior (Authorization plus
    x-goog-user-project when a quota project is configured).
    """

    def __init__(self, credentials: GoogleCredentials) -> None:
        self._credentials = credentials
        self._lock = asyncio.Lock()
        self._generation = 0

    @property
    def generation(self) -> int:
        return self._generation

    def apply_auth(self, headers: dict[str, str]) -> None:
        self._credentials.apply(headers)

    async def refresh(self, observed_generation: int) -> None:
        async with self._lock:
            if self._generation > observed_generation:
                return
            await asyncio.to_thread(self._credentials.refresh, Request())
            self._generation += 1


async def _authed_get(
    http_client: httpx.AsyncClient,
    url: str,
    token_manager: _TokenManager,
    accept: str | None = None,
) -> httpx.Response:
    """GET with token-manager auth. Refreshes credentials once on 401, otherwise raises."""
    for attempt in range(2):
        observed_generation = token_manager.generation
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        token_manager.apply_auth(headers)
        resp = await http_client.get(url, headers=headers, timeout=30.0)
        if resp.status_code == 401 and attempt == 0:
            logger.debug("Got 401 from %s, refreshing GCP credentials", url)
            await token_manager.refresh(observed_generation)
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError(f"unreachable: exhausted retries fetching {url}")


async def _fetch_json(
    http_client: httpx.AsyncClient,
    url: str,
    token_manager: _TokenManager,
    accept: str | None = None,
) -> dict[str, Any]:
    resp = await _authed_get(http_client, url, token_manager, accept)
    return resp.json()


async def _fetch_manifest_with_digest(
    http_client: httpx.AsyncClient,
    url: str,
    token_manager: _TokenManager,
    accept: str,
) -> tuple[dict[str, Any], str | None]:
    resp = await _authed_get(http_client, url, token_manager, accept)
    return resp.json(), resp.headers.get("Docker-Content-Digest")


async def _fetch_image_config(
    http_client: httpx.AsyncClient,
    token_manager: _TokenManager,
    registry: str,
    image_path: str,
    reference: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch OCI image config and return (config, manifest_digest).

    Returns (None, None) when the manifest legitimately has no enrichable config
    (attestation manifest, missing config descriptor, attestation media type).
    Raises on fetch/decode errors.
    """
    manifest_url = build_manifest_url(registry, image_path, reference)
    manifest, manifest_digest = await _fetch_manifest_with_digest(
        http_client,
        manifest_url,
        token_manager,
        ALL_MANIFEST_ACCEPT,
    )

    # Skip attestation manifests (they reference a subject image, not a runnable config)
    if manifest.get("subject"):
        return None, None

    config_descriptor = manifest.get("config") or {}
    config_digest = config_descriptor.get("digest")
    config_media_type = config_descriptor.get("mediaType", "")

    if not config_digest:
        return None, None
    if any(
        frag in config_media_type.lower() for frag in ATTESTATION_MEDIA_TYPE_FRAGMENTS
    ):
        return None, None

    blob_url = build_blob_url(registry, image_path, config_digest)
    config = await _fetch_json(http_client, blob_url, token_manager)
    return config, manifest_digest


async def _fetch_attestation_provenance(
    http_client: httpx.AsyncClient,
    token_manager: _TokenManager,
    registry: str,
    image_path: str,
    image_digest: str,
) -> dict[str, str]:
    """Attempt to find SLSA provenance via the OCI Referrers API.

    The Referrers endpoint and individual attestation blobs are best-effort:
    HTTP 404 means "no attestations" and is treated as no-op, but other
    HTTP/decode errors propagate so the caller can flag the image as failed.
    """
    referrers_url = f"https://{registry}/v2/{image_path}/referrers/{image_digest}"
    try:
        index = await _fetch_json(http_client, referrers_url, token_manager)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {}
        raise

    for ref_manifest in index.get("manifests") or []:
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
        try:
            att_manifest = await _fetch_json(
                http_client, att_manifest_url, token_manager
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                continue
            raise

        for layer in att_manifest.get("layers") or []:
            layer_mt = layer.get("mediaType", "").lower()
            if "in-toto" not in layer_mt and "provenance" not in layer_mt:
                continue

            layer_digest = layer.get("digest")
            if not layer_digest:
                continue

            blob_url = build_blob_url(registry, image_path, layer_digest)
            try:
                blob = await _fetch_json(http_client, blob_url, token_manager)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    continue
                raise

            predicate = decode_attestation_blob_to_predicate(blob)
            if predicate is None:
                continue
            provenance = extract_image_source_provenance(predicate)
            if provenance:
                return provenance

    return {}


async def _process_single_image(
    http_client: httpx.AsyncClient,
    token_manager: _TokenManager,
    artifact: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    """Process one image: fetch config, extract provenance + layers.

    Returns (enrichment_or_none, fetch_failed). `fetch_failed` is True when the
    image's config or attestation could not be fetched due to a transient or
    unexpected error; callers use it to decide whether stale-layer cleanup is
    safe.
    """
    name = artifact.get("name", "")
    uri = artifact.get("uri", "")
    media_type = artifact.get("mediaType", "")

    if media_type not in SINGLE_IMAGE_MEDIA_TYPES:
        logger.debug("Skipping OCI config enrichment for non-image artifact %s", name)
        return None, False

    parsed = parse_docker_image_uri(uri)
    if not parsed:
        return None, False

    registry, image_path, reference = parsed

    try:
        config, manifest_digest = await _fetch_image_config(
            http_client, token_manager, registry, image_path, reference
        )
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.warning(
            "Failed to fetch image config for %s: %s",
            uri or name,
            e,
        )
        return None, True
    if not config:
        return None, False

    raw_architecture = config.get("architecture")
    architecture = (
        normalize_architecture(raw_architecture)
        if raw_architecture is not None
        else None
    )
    os_name = config.get("os")
    variant = config.get("variant")
    provenance = extract_provenance_from_oci_config(config)
    fetch_failed = False

    # OCI labels are fast but not always present; fall back to the Referrers API.
    # The Referrers endpoint requires a digest, not a tag.
    if not provenance.get("source_uri"):
        subject_digest = uri.split("@")[-1] if "@" in uri else manifest_digest
        if subject_digest and subject_digest.startswith("sha256:"):
            try:
                slsa_provenance = await _fetch_attestation_provenance(
                    http_client,
                    token_manager,
                    registry,
                    image_path,
                    subject_digest,
                )
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                logger.warning(
                    "Failed to fetch attestation provenance for %s: %s",
                    uri or name,
                    e,
                )
                slsa_provenance = {}
                fetch_failed = True
            provenance.update(slsa_provenance)

    diff_ids, layer_history = extract_layers_from_oci_config(config)
    has_platform = any(value is not None for value in (architecture, os_name, variant))

    if not provenance.get("source_uri") and not diff_ids and not has_platform:
        return None, fetch_failed

    result: dict[str, Any] = {
        "id": name,
    }
    if architecture is not None:
        result["architecture"] = architecture
    if os_name is not None:
        result["os"] = os_name
    if variant is not None:
        result["variant"] = variant
    if provenance.get("source_uri"):
        result["source_uri"] = provenance["source_uri"]
    if provenance.get("source_revision"):
        result["source_revision"] = provenance["source_revision"]
    if provenance.get("source_file"):
        result["source_file"] = provenance["source_file"]
    if diff_ids:
        result["layer_diff_ids"] = diff_ids
        result["layer_history"] = layer_history

    return result, fetch_failed


async def _fetch_all_image_provenance(
    credentials: GoogleCredentials | None,
    docker_artifacts_raw: list[dict[str, Any]],
    project_id: str,
    max_concurrent: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Run enrichment for all single-image artifacts.

    Returns (results, fetch_failures). `fetch_failures` is the count of images
    that hit a transient fetch error; callers use it to suppress stale-layer
    cleanup when the enrichment pass was incomplete.
    """
    resolved = _resolve_credentials(credentials)
    if not resolved.valid:
        resolved.refresh(Request())
    token_manager = _TokenManager(resolved)

    single_images = [
        a
        for a in docker_artifacts_raw
        if a.get("mediaType", "") in SINGLE_IMAGE_MEDIA_TYPES
    ]
    if not single_images:
        return [], 0

    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[dict[str, Any]] = []
    fetch_failures = 0

    async def bounded_process(
        artifact: dict[str, Any], client: httpx.AsyncClient
    ) -> tuple[dict[str, Any] | None, bool]:
        async with semaphore:
            return await _process_single_image(client, token_manager, artifact)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [asyncio.create_task(bounded_process(a, client)) for a in single_images]
        total = len(tasks)

        logger.info("Fetching OCI configs for %d single-image artifacts...", total)
        progress_interval = max(1, min(100, total // 10 or 1))
        completed = 0

        for task in asyncio.as_completed(tasks):
            result, failed = await task
            completed += 1
            if failed:
                fetch_failures += 1
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
        "Extracted provenance/layer data for %d of %d images (%d fetch failures)",
        len(results),
        total,
        fetch_failures,
    )
    return results, fetch_failures


def _build_layer_dicts(
    enrichments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate and build ImageLayer node dicts from enrichment results.

    Creates a node for every diff_id. History commands are matched to
    diff_ids by skipping empty-layer entries (which have no diff_id),
    but layers are still created even when history is absent or truncated.
    When the same diff_id is observed in multiple images, a populated
    history entry takes precedence over a missing one.
    """
    layers_by_diff_id: dict[str, dict[str, Any]] = {}

    for enrichment in enrichments:
        diff_ids = enrichment.get("layer_diff_ids", [])
        history_entries = enrichment.get("layer_history", [])

        history_by_idx: dict[int, str | None] = {}
        non_empty_idx = 0
        for entry in history_entries:
            if entry.get("empty_layer", False):
                continue
            history_by_idx[non_empty_idx] = entry.get("created_by") or None
            non_empty_idx += 1

        for idx, diff_id in enumerate(diff_ids):
            history = history_by_idx.get(idx)
            existing = layers_by_diff_id.get(diff_id)
            if existing is None:
                layers_by_diff_id[diff_id] = {
                    "diff_id": diff_id,
                    "history": history,
                }
            elif existing.get("history") is None and history is not None:
                existing["history"] = history

    return list(layers_by_diff_id.values())


@timeit
def load_image_provenance(
    neo4j_session: neo4j.Session,
    provenance_updates: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    if not provenance_updates:
        return

    load_nodes_without_relationships(
        neo4j_session,
        GCPArtifactRegistryContainerImageProvenanceSchema(),
        provenance_updates,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry container image provenance updates for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_image_layers(
    neo4j_session: neo4j.Session,
    layer_dicts: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    if not layer_dicts:
        return

    schema = GCPArtifactRegistryImageLayerSchema()
    load_nodes_without_relationships(
        neo4j_session,
        schema,
        layer_dicts,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry image layer nodes for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryProjectToImageLayerRel(),
        layer_dicts,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry image layer project RESOURCE relationships for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: GoogleCredentials | None,
    docker_artifacts_raw: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    cleanup_safe: bool = True,
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

    enrichments, fetch_failures = loop.run_until_complete(
        _fetch_all_image_provenance(credentials, docker_artifacts_raw, project_id),
    )

    if enrichments:
        provenance_updates = [
            {
                "id": e["id"],
                "source_uri": e.get("source_uri"),
                "source_revision": e.get("source_revision"),
                "source_file": e.get("source_file"),
                "layer_diff_ids": e.get("layer_diff_ids"),
                "architecture": e.get("architecture"),
                "os": e.get("os"),
                "variant": e.get("variant"),
            }
            for e in enrichments
        ]
        load_image_provenance(
            neo4j_session,
            provenance_updates,
            project_id,
            update_tag,
        )

    layer_dicts = _build_layer_dicts(enrichments)
    if layer_dicts:
        load_image_layers(neo4j_session, layer_dicts, project_id, update_tag)

    # Stale-layer cleanup is only safe when artifact discovery was complete AND
    # the enrichment pass had no fetch failures. Discovery completeness governs
    # whether the input image set is authoritative; fetch-failure gating
    # protects against deleting layers whose images we simply could not
    # re-fetch this run. We still run cleanup when enrichments is empty (e.g.,
    # all images deleted, or no enrichable artifacts left), so orphan layer
    # nodes do not accumulate.
    skip_reasons = []
    if not cleanup_safe:
        skip_reasons.append("artifact discovery was incomplete")
    if fetch_failures:
        skip_reasons.append(f"{fetch_failures} image(s) failed to enrich")

    if skip_reasons:
        logger.warning(
            "Skipping image layer cleanup for project %s: %s.",
            project_id,
            "; ".join(skip_reasons),
        )
    else:
        cleanup_params = common_job_parameters.copy()
        cleanup_params["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            GCPArtifactRegistryImageLayerSchema(),
            cleanup_params,
        ).run(neo4j_session)
        # The split write path attaches this relationship with a MatchLink, so
        # clean it explicitly after node cleanup has used the project RESOURCE
        # edge to scope stale node deletion.
        GraphJob.from_matchlink(
            GCPArtifactRegistryProjectToImageLayerRel(),
            "GCPProject",
            project_id,
            update_tag,
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
