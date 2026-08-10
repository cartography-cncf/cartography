"""Enrich Scaleway Container Registry images with supply-chain data.

Scaleway's management SDK does not expose image layers or provenance, but the
registry endpoint (``rg.<region>.scw.cloud``) is a standard OCI Distribution v2
registry. This module fetches each image's OCI manifest + config (authenticating
with the Scaleway secret key as a registry Bearer token) and enriches the
``ScalewayContainerRegistryImage`` node with:

* ``layer_diff_ids`` + ``ScalewayContainerRegistryImageLayer`` nodes -- feed the
  shared supply-chain *dockerfile-matching* arm.
* ``source_uri`` / ``source_revision`` / ``source_file`` -- the *provenance* arm,
  parsed from OCI labels/annotations (``org.opencontainers.image.source``) and,
  when present, the buildx SLSA attestation manifest carried in the image index.

The GitHub/GitLab supply-chain matchers then draw ``PACKAGED_FROM`` edges from
these images to their source repositories; nothing registry-specific is needed
there because those matchers key on the generic ``:Image`` / ``:ImageLayer``
labels and on ``source_uri``.
"""

import base64
import logging
from typing import Any

import httpx
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.intel.container_image_layers import ContainerImageLayerGraphShape
from cartography.intel.container_image_layers import get_complete_layer_digests
from cartography.intel.container_image_layers import refresh_layer_closures
from cartography.intel.supply_chain import decode_attestation_blob_to_predicate
from cartography.intel.supply_chain import extract_image_source_provenance
from cartography.intel.supply_chain import extract_layers_from_oci_config
from cartography.intel.supply_chain import extract_provenance_from_oci_config
from cartography.intel.supply_chain import normalize_vcs_url
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageEnrichmentSchema,
)
from cartography.models.scaleway.container_registry.image_layer import (
    ScalewayContainerRegistryImageLayerSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

SCALEWAY_LAYER_GRAPH = ContainerImageLayerGraphShape(
    image_label="ScalewayContainerRegistryImage",
    layer_label="ScalewayContainerRegistryImageLayer",
    scope_label="ScalewayProject",
    scope_properties=("id",),
    image_layer_rel_types=("HAS_LAYER",),
    stable_image_rel_types=(),
)

_HTTP_TIMEOUT = 30.0
_MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)
# Attestation manifests reference a subject image, not a runnable config.
_ATTESTATION_REFERENCE_TYPE = "attestation-manifest"
_INTOTO_MEDIA_TYPE = "application/vnd.in-toto+json"
_OCI_SOURCE_ANNOTATION = "org.opencontainers.image.source"
_OCI_REVISION_ANNOTATION = "org.opencontainers.image.revision"
_PROVENANCE_FIELDS = ("source_uri", "source_revision", "source_file")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    secret_key: str,
    common_job_parameters: dict[str, Any],
    projects_id: list[str],
    update_tag: int,
) -> None:
    images_to_enrich = _get_images_to_enrich(neo4j_session)
    skipped_by_project: dict[str, set[str]] = {}
    for project_id in projects_id:
        project_images = [
            image for image in images_to_enrich if image.get("project_id") == project_id
        ]
        complete_digests = get_complete_layer_digests(
            neo4j_session,
            SCALEWAY_LAYER_GRAPH,
            (str(image["digest"]) for image in project_images if image.get("digest")),
            {"id": project_id},
        )
        skipped_by_project[project_id] = complete_digests

    raw, fetch_failed = get(
        neo4j_session,
        secret_key,
        images_to_enrich=images_to_enrich,
        cached_layer_keys={
            (project_id, digest)
            for project_id, digests in skipped_by_project.items()
            for digest in digests
        },
    )
    images_by_project, layers_by_project = transform(raw)
    images_by_project = _merge_existing_image_enrichments(
        neo4j_session,
        images_by_project,
    )
    load_supply_chain(neo4j_session, images_by_project, layers_by_project, update_tag)
    for project_id, skipped_digests in skipped_by_project.items():
        refresh_layer_closures(
            neo4j_session,
            SCALEWAY_LAYER_GRAPH,
            skipped_digests,
            {"id": project_id},
            update_tag,
        )
    if fetch_failed:
        # A transient registry error (timeout/401/5xx) on any image means we did
        # not refresh that image's layers this run. Skipping cleanup avoids
        # deleting layer nodes (and their HAS_LAYER edges) that are merely
        # stale-tagged, not actually gone; they get cleaned on a clean run.
        logger.warning(
            "Skipping Scaleway image-layer cleanup: one or more OCI fetches failed."
        )
        return
    cleanup(neo4j_session, projects_id, common_job_parameters)


def _parse_image_uri(uri: str) -> tuple[str, str, str] | None:
    """Split a tag URI (``rg.<region>.scw.cloud/<ns>/<img>:<tag>``) into
    (registry_host, region, repo_path)."""
    host, _, remainder = uri.partition("/")
    if not remainder:
        return None
    host_parts = host.split(".")
    if len(host_parts) < 4 or host_parts[0] != "rg":
        return None
    region = host_parts[1]
    repo_path = remainder.rsplit(":", 1)[0]
    return host, region, repo_path


def _registry_token(host: str, region: str, repo_path: str, secret_key: str) -> str:
    realm = f"https://api.scaleway.com/registry-internal/v1/regions/{region}/tokens"
    auth = base64.b64encode(f"nologin:{secret_key}".encode()).decode()
    resp = httpx.get(
        realm,
        params={"service": "registry", "scope": f"repository:{repo_path}:pull"},
        headers={"Authorization": f"Basic {auth}"},
        timeout=_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def _get_json(client: httpx.Client, url: str, accept: str) -> dict[str, Any]:
    resp = client.get(url, headers={"Accept": accept})
    resp.raise_for_status()
    return resp.json()


def _fetch_config(
    client: httpx.Client, base: str, manifest: dict[str, Any]
) -> dict[str, Any] | None:
    config_descriptor = manifest.get("config") or {}
    config_digest = config_descriptor.get("digest")
    if not config_digest:
        return None
    return _get_json(
        client,
        f"{base}/blobs/{config_digest}",
        config_descriptor.get("mediaType", "application/vnd.oci.image.config.v1+json"),
    )


def _fetch_attestation_predicate(
    client: httpx.Client, base: str, attestation_digest: str
) -> dict[str, Any] | None:
    """Fetch a buildx attestation manifest and return its SLSA provenance predicate."""
    att_manifest = _get_json(
        client, f"{base}/manifests/{attestation_digest}", _MANIFEST_ACCEPT
    )
    for layer in att_manifest.get("layers") or []:
        if layer.get("mediaType") != _INTOTO_MEDIA_TYPE:
            continue
        predicate_type = (layer.get("annotations") or {}).get(
            "in-toto.io/predicate-type", ""
        )
        if "slsa.dev/provenance" not in predicate_type:
            continue
        blob = _get_json(client, f"{base}/blobs/{layer['digest']}", _INTOTO_MEDIA_TYPE)
        predicate = decode_attestation_blob_to_predicate(blob)
        if predicate:
            return predicate
    return None


def fetch_image_supply_chain(
    host: str,
    region: str,
    repo_path: str,
    reference: str,
    secret_key: str,
    *,
    fetch_config: bool = True,
) -> tuple[
    dict[str, Any] | None,
    dict[str, str],
    dict[str, Any] | None,
    bool,
]:
    """Fetch OCI supply-chain data for an image reference.

    Returns ``(config, annotations, attestation_predicate,
    attestation_fetch_failed)``, resolving a multi-arch index to its runnable
    platform manifest and, if present, its buildx SLSA attestation manifest.
    ``config``/``predicate`` are None when absent; ``annotations`` merges index
    + platform manifest annotations.
    """
    token = _registry_token(host, region, repo_path, secret_key)
    base = f"https://{host}/v2/{repo_path}"
    annotations: dict[str, str] = {}
    attestation_predicate: dict[str, Any] | None = None
    attestation_fetch_failed = False
    # Blob reads 307-redirect to object storage; httpx drops the Authorization
    # header on the cross-host hop, so the presigned URL authenticates itself.
    with httpx.Client(
        headers={"Authorization": f"Bearer {token}"},
        timeout=_HTTP_TIMEOUT,
        follow_redirects=True,
    ) as client:
        manifest = _get_json(client, f"{base}/manifests/{reference}", _MANIFEST_ACCEPT)
        annotations.update(manifest.get("annotations") or {})
        # Resolve an index to a concrete platform image manifest (and grab the
        # attestation manifest for SLSA provenance, if any).
        if manifest.get("manifests"):
            platform_digest = None
            for entry in manifest["manifests"]:
                entry_ann = entry.get("annotations") or {}
                if (
                    entry_ann.get("vnd.docker.reference.type")
                    == _ATTESTATION_REFERENCE_TYPE
                ):
                    try:
                        attestation_predicate = _fetch_attestation_predicate(
                            client, base, entry["digest"]
                        )
                    except httpx.HTTPError as exc:
                        logger.warning(
                            "Attestation fetch failed for %s: %s",
                            base,
                            exc,
                        )
                        attestation_fetch_failed = True
                    continue
                platform = entry.get("platform") or {}
                if platform.get("os") in (None, "unknown"):
                    continue
                if platform_digest is None:
                    platform_digest = entry.get("digest")
            if platform_digest is None:
                return (
                    None,
                    annotations,
                    attestation_predicate,
                    attestation_fetch_failed,
                )
            if not fetch_config:
                return (
                    None,
                    annotations,
                    attestation_predicate,
                    attestation_fetch_failed,
                )
            manifest = _get_json(
                client, f"{base}/manifests/{platform_digest}", _MANIFEST_ACCEPT
            )
            annotations.update(manifest.get("annotations") or {})
        config = _fetch_config(client, base, manifest) if fetch_config else None
    return config, annotations, attestation_predicate, attestation_fetch_failed


def _get_images_to_enrich(
    neo4j_session: neo4j.Session,
) -> list[dict[str, Any]]:
    """Return the digest/project/uri of every Scaleway registry image to enrich.

    An image digest is deduplicated globally, so the same node can belong to
    several projects. Scope the tag to the same project as the image so the pull
    URI is always project-local (never a repository from another project).
    """
    result = neo4j_session.run(
        """
        MATCH (p:ScalewayProject)-[:RESOURCE]->(i:ScalewayContainerRegistryImage)
        MATCH (p)-[:RESOURCE]->(t:ScalewayContainerRegistryImageTag)-[:IMAGE]->(i)
        WITH i, p, collect(t.uri) AS uris
        RETURN i.digest AS digest, p.id AS project_id, uris[0] AS uri
        """
    )
    return [dict(record) for record in result]


@timeit
def get(
    neo4j_session: neo4j.Session,
    secret_key: str,
    *,
    images_to_enrich: list[dict[str, Any]] | None = None,
    cached_layer_keys: set[tuple[str, str]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch the OCI config for every Scaleway registry image.

    Returns ``(enriched, fetch_failed)`` where ``fetch_failed`` is True if any
    image's OCI fetch hit a transient registry error, so the caller can skip
    layer cleanup and avoid deleting layers it could not refresh this run.
    """
    enriched: list[dict[str, Any]] = []
    fetch_failed = False
    candidates = (
        images_to_enrich
        if images_to_enrich is not None
        else _get_images_to_enrich(neo4j_session)
    )
    cached_layer_keys = cached_layer_keys or set()
    for image in candidates:
        uri = image.get("uri")
        digest = image.get("digest")
        if not uri or not digest:
            continue
        parsed = _parse_image_uri(uri)
        if parsed is None:
            logger.warning("Unparseable Scaleway image URI, skipping: %s", uri)
            continue
        host, region, repo_path = parsed
        try:
            (
                config,
                annotations,
                attestation_predicate,
                attestation_fetch_failed,
            ) = fetch_image_supply_chain(
                host,
                region,
                repo_path,
                digest,
                secret_key,
                fetch_config=(str(image["project_id"]), str(digest))
                not in cached_layer_keys,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "Failed to fetch OCI data for %s@%s: %s", repo_path, digest, exc
            )
            fetch_failed = True
            continue
        fetch_failed = fetch_failed or attestation_fetch_failed
        if (
            config is None
            and attestation_predicate is None
            and not _provenance_from_annotations(annotations)
        ):
            continue
        enriched.append(
            {
                "digest": digest,
                "project_id": image["project_id"],
                "config": config,
                "annotations": annotations,
                "attestation_predicate": attestation_predicate,
            }
        )
    return enriched, fetch_failed


def _provenance_from_annotations(annotations: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    source = annotations.get(_OCI_SOURCE_ANNOTATION)
    if source:
        result["source_uri"] = normalize_vcs_url(source)
    revision = annotations.get(_OCI_REVISION_ANNOTATION)
    if revision:
        result["source_revision"] = revision
    return result


def _resolve_provenance(entry: dict[str, Any]) -> dict[str, str]:
    """Coalesce source provenance from the SLSA attestation, OCI config labels,
    and manifest annotations (in that order of authority)."""
    predicate = entry.get("attestation_predicate")
    sources = [
        extract_image_source_provenance(predicate) if predicate else {},
        (
            extract_provenance_from_oci_config(entry["config"])
            if entry.get("config")
            else {}
        ),
        _provenance_from_annotations(entry.get("annotations") or {}),
    ]
    provenance: dict[str, str] = {}
    for source in sources:
        for field in _PROVENANCE_FIELDS:
            value = source.get(field)
            if value and not provenance.get(field):
                provenance[field] = value
    return provenance


def transform(
    raw: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    images_by_project: dict[str, list[dict[str, Any]]] = {}
    layers_by_project: dict[str, list[dict[str, Any]]] = {}

    for entry in raw:
        project_id = entry["project_id"]
        config = entry.get("config")
        provenance = _resolve_provenance(entry)

        image_update: dict[str, Any] = {
            "digest": entry["digest"],
        }
        if config:
            diff_ids, layer_history = extract_layers_from_oci_config(config)
            image_update["layer_diff_ids"] = diff_ids
        else:
            diff_ids, layer_history = [], []
        image_update.update(
            {
                field: provenance[field]
                for field in _PROVENANCE_FIELDS
                if provenance.get(field)
            },
        )
        if len(image_update) == 1:
            continue
        images_by_project.setdefault(project_id, []).append(image_update)

        if not diff_ids:
            continue

        # Align each non-empty history command to its diff_id (empty layers such
        # as ENV/WORKDIR carry no diff_id). Standard OCI: the count of non-empty
        # history entries equals len(diff_ids).
        project_layers = layers_by_project.setdefault(project_id, [])
        idx = 0
        for record in layer_history:
            if record.get("empty_layer"):
                continue
            if idx >= len(diff_ids):
                break
            project_layers.append(
                {
                    "diff_id": diff_ids[idx],
                    "history": record.get("created_by", ""),
                    "is_empty": False,
                }
            )
            idx += 1

    return images_by_project, layers_by_project


def _merge_existing_image_enrichments(
    neo4j_session: neo4j.Session,
    images_by_project: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Preserve immutable layers and previously discovered provenance."""
    merged_by_project: dict[str, list[dict[str, Any]]] = {}
    fields = ("layer_diff_ids", *_PROVENANCE_FIELDS)
    for project_id, updates in images_by_project.items():
        digests = sorted(
            {str(update["digest"]) for update in updates if update.get("digest")}
        )
        existing_rows = neo4j_session.execute_read(
            read_list_of_dicts_tx,
            """
            MATCH (:ScalewayProject {id: $project_id})-[:RESOURCE]->
                  (image:ScalewayContainerRegistryImage)
            WHERE image.digest IN $digests
            RETURN
                image.digest AS digest,
                image.layer_diff_ids AS layer_diff_ids,
                image.source_uri AS source_uri,
                image.source_revision AS source_revision,
                image.source_file AS source_file
            """,
            project_id=project_id,
            digests=digests,
        )
        existing_by_digest = {row["digest"]: row for row in existing_rows}
        merged_updates = []
        for update in updates:
            merged = {
                "digest": update["digest"],
                **{
                    field: existing_by_digest.get(update["digest"], {}).get(field)
                    for field in fields
                },
            }
            merged.update(
                {field: value for field, value in update.items() if value is not None},
            )
            merged_updates.append(merged)
        merged_by_project[project_id] = merged_updates
    return merged_by_project


@timeit
def load_supply_chain(
    neo4j_session: neo4j.Session,
    images_by_project: dict[str, list[dict[str, Any]]],
    layers_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    # Layers before the image enrichment so the image HAS_LAYER edges resolve.
    for project_id, layers in layers_by_project.items():
        load(
            neo4j_session,
            ScalewayContainerRegistryImageLayerSchema(),
            layers,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, images in images_by_project.items():
        load(
            neo4j_session,
            ScalewayContainerRegistryImageEnrichmentSchema(),
            images,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayContainerRegistryImageLayerSchema(), scoped_job_parameters
        ).run(neo4j_session)
