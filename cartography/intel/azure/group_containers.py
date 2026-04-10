import logging
from typing import Any

import neo4j
import requests as http_requests
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.group_container import AzureGroupContainerSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)

_ARCH_NORMALIZATION_MAP = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def get_architecture(
    registry: str, repo: str, digest: str, credential: Any
) -> str | None:
    """
    Fetches the raw CPU architecture string for an ACR image by digest.
    Exchanges an AAD token for an ACR access token, fetches the OCI manifest
    to get the config blob digest, then fetches the config blob to read
    the architecture field.
    Returns the raw value (e.g. "amd64", "arm64") or None if unavailable.
    """
    try:
        aad_token = credential.get_token("https://management.azure.com/.default").token

        refresh_resp = http_requests.post(
            f"https://{registry}/oauth2/exchange",
            data={
                "grant_type": "access_token",
                "service": registry,
                "access_token": aad_token,
            },
            timeout=10,
        )
        refresh_resp.raise_for_status()
        refresh_token = refresh_resp.json()["refresh_token"]

        access_resp = http_requests.post(
            f"https://{registry}/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "service": registry,
                "scope": f"repository:{repo}:pull",
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
        access_resp.raise_for_status()
        token = access_resp.json()["access_token"]

        manifest_resp = http_requests.get(
            f"https://{registry}/v2/{repo}/manifests/{digest}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.oci.image.manifest.v1+json",
            },
            timeout=10,
        )
        manifest_resp.raise_for_status()
        config_digest = manifest_resp.json()["config"]["digest"]

        blob_resp = http_requests.get(
            f"https://{registry}/v2/{repo}/blobs/{config_digest}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
            allow_redirects=True,
        )
        blob_resp.raise_for_status()
        return blob_resp.json().get("architecture")
    except Exception as e:
        logger.warning(
            f"Failed to fetch architecture for {registry}/{repo}@{digest}: {e}"
        )
        return None


@timeit
def get_container_groups(credentials: Credentials, subscription_id: str) -> list[dict]:
    try:
        client = ContainerInstanceManagementClient(
            credentials.credential, subscription_id
        )
        return [cg.as_dict() for cg in client.container_groups.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get container groups for subscription {subscription_id}: {str(e)}"
        )
        return []


def get_container_architectures(
    raw_groups: list[dict],
    credentials: Credentials,
) -> dict[str, dict[str, str | None]]:
    """
    For each unique digest-pinned ACR image across all container groups,
    fetches the normalized architecture from the OCI image config blob.

    Only queries ACR registries (*.azurecr.io). Non-ACR images and
    tag-based references produce no entry (architecture will be None).

    Returns a dict mapping image_digest -> architecture_normalized.
    """
    targets: dict[str, tuple[str, str]] = {}  # digest -> (registry, repo)
    for group in raw_groups:
        for container in group.get("containers", []):
            image = container.get("image", "")
            if not image or "@" not in image:
                continue
            ref, digest = image.split("@", 1)
            if ".azurecr.io/" not in ref:
                continue
            registry, repo = ref.split("/", 1)
            if digest not in targets:
                targets[digest] = (registry, repo)

    architecture_map: dict[str, dict[str, str | None]] = {}
    for digest, (registry, repo) in targets.items():
        raw_arch = get_architecture(registry, repo, digest, credentials.credential)
        architecture_map[digest] = {
            "architecture": raw_arch,
            "architecture_normalized": (
                _ARCH_NORMALIZATION_MAP.get(raw_arch, raw_arch) if raw_arch else None
            ),
            "architecture_source": "acr_manifest" if raw_arch else None,
        }
    return architecture_map


def transform_group_containers(
    container_groups: list[dict],
    architecture_map: dict[str, dict[str, str | None]],
) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for group in container_groups:
        group_id = group.get("id")
        for container in group.get("containers", []):
            image = container.get("image")
            try:
                image_digest = image.split("@")[1] if image else None
            except IndexError:
                image_digest = None

            resources = container.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            arch_info: dict[str, str | None] = (
                architecture_map.get(image_digest, {}) if image_digest else {}
            )
            transformed.append(
                {
                    "id": f"{group_id}/{container.get('name')}",
                    "name": container.get("name"),
                    "group_id": group_id,
                    "image": image,
                    "image_digest": image_digest,
                    "architecture": arch_info.get("architecture"),
                    "architecture_normalized": arch_info.get("architecture_normalized"),
                    "architecture_source": arch_info.get("architecture_source"),
                    "cpu_request": requests.get("cpu"),
                    "memory_request_gb": requests.get("memory_in_gb"),
                    "cpu_limit": limits.get("cpu"),
                    "memory_limit_gb": limits.get("memory_in_gb"),
                },
            )
    return transformed


@timeit
def load_group_containers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureGroupContainerSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_group_containers(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(AzureGroupContainerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_group_containers(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Group Containers for subscription {subscription_id}.")
    raw_groups = get_container_groups(credentials, subscription_id)
    architecture_map = get_container_architectures(raw_groups, credentials)
    transformed = transform_group_containers(raw_groups, architecture_map)
    load_group_containers(neo4j_session, transformed, subscription_id, update_tag)
    cleanup_group_containers(neo4j_session, common_job_parameters)
