"""Enrich Scaleway Container Registry images with supply-chain data.

Scaleway's management SDK does not expose image layers or provenance, but the
registry endpoint (``rg.<region>.scw.cloud``) is a standard OCI Distribution v2
registry. This module fetches each image's OCI manifest + config (authenticating
with the Scaleway secret key as a registry Bearer token) and enriches the
``ScalewayContainerRegistryImage`` node with:

* ``layer_diff_ids`` + ``ScalewayContainerRegistryImageLayer`` nodes -- feed the
  shared supply-chain *dockerfile-matching* arm.

The GitHub/GitLab supply-chain matchers then draw ``PACKAGED_FROM`` edges from
these images to their source repositories; nothing registry-specific is needed
there because those matchers key on the generic ``:Image`` / ``:ImageLayer``
labels.
"""

import base64
import logging
from typing import Any

import httpx
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supply_chain import extract_layers_from_oci_config
from cartography.models.scaleway.container_registry.image import (
    ScalewayContainerRegistryImageSchema,
)
from cartography.models.scaleway.container_registry.image_layer import (
    ScalewayContainerRegistryImageLayerSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

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


@timeit
def sync(
    neo4j_session: neo4j.Session,
    secret_key: str,
    common_job_parameters: dict[str, Any],
    projects_id: list[str],
    update_tag: int,
) -> None:
    raw = get(neo4j_session, secret_key)
    images_by_project, layers_by_project = transform(raw)
    load_supply_chain(neo4j_session, images_by_project, layers_by_project, update_tag)
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


def fetch_image_config(
    host: str,
    region: str,
    repo_path: str,
    reference: str,
    secret_key: str,
) -> dict[str, Any] | None:
    """Fetch and return the OCI image config JSON for an image reference.

    Resolves a multi-arch index to its first runnable platform manifest. Returns
    None when there is no enrichable config (e.g. an attestation-only manifest).
    """
    token = _registry_token(host, region, repo_path, secret_key)
    base = f"https://{host}/v2/{repo_path}"
    with httpx.Client(
        headers={"Authorization": f"Bearer {token}"}, timeout=_HTTP_TIMEOUT
    ) as client:
        manifest = _get_json(client, f"{base}/manifests/{reference}", _MANIFEST_ACCEPT)
        # Resolve an index to a concrete platform image manifest.
        if manifest.get("manifests"):
            platform_digest = None
            for entry in manifest["manifests"]:
                ann = entry.get("annotations") or {}
                if ann.get("vnd.docker.reference.type") == _ATTESTATION_REFERENCE_TYPE:
                    continue
                platform = entry.get("platform") or {}
                if platform.get("os") in (None, "unknown"):
                    continue
                platform_digest = entry.get("digest")
                break
            if platform_digest is None:
                return None
            manifest = _get_json(
                client, f"{base}/manifests/{platform_digest}", _MANIFEST_ACCEPT
            )
        config_descriptor = manifest.get("config") or {}
        config_digest = config_descriptor.get("digest")
        if not config_digest:
            return None
        return _get_json(
            client,
            f"{base}/blobs/{config_digest}",
            config_descriptor.get(
                "mediaType", "application/vnd.oci.image.config.v1+json"
            ),
        )


def _get_images_to_enrich(
    neo4j_session: neo4j.Session,
) -> list[dict[str, Any]]:
    """Return the digest/project/uri of every Scaleway registry image to enrich."""
    result = neo4j_session.run(
        """
        MATCH (p:ScalewayProject)-[:RESOURCE]->(i:ScalewayContainerRegistryImage)
        MATCH (i)<-[:IMAGE]-(t:ScalewayContainerRegistryImageTag)
        WITH i, p, collect(t.uri) AS uris
        RETURN i.digest AS digest, p.id AS project_id, uris[0] AS uri
        """
    )
    return [dict(record) for record in result]


@timeit
def get(neo4j_session: neo4j.Session, secret_key: str) -> list[dict[str, Any]]:
    """Fetch the OCI config for every Scaleway registry image."""
    enriched: list[dict[str, Any]] = []
    for image in _get_images_to_enrich(neo4j_session):
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
            config = fetch_image_config(host, region, repo_path, digest, secret_key)
        except httpx.HTTPError as exc:
            logger.warning(
                "Failed to fetch OCI config for %s@%s: %s", repo_path, digest, exc
            )
            continue
        if config is None:
            continue
        enriched.append(
            {
                "digest": digest,
                "project_id": image["project_id"],
                "config": config,
            }
        )
    return enriched


def transform(
    raw: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    images_by_project: dict[str, list[dict[str, Any]]] = {}
    layers_by_project: dict[str, list[dict[str, Any]]] = {}

    for entry in raw:
        project_id = entry["project_id"]
        config = entry["config"]
        diff_ids, layer_history = extract_layers_from_oci_config(config)
        if not diff_ids:
            continue

        image_update: dict[str, Any] = {
            "digest": entry["digest"],
            "layer_diff_ids": diff_ids,
        }
        images_by_project.setdefault(project_id, []).append(image_update)

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
            ScalewayContainerRegistryImageSchema(),
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
