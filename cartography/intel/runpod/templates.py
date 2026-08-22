from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.pods import _port_summaries
from cartography.intel.runpod.util import first_not_none
from cartography.intel.runpod.util import first_present
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.template import RunPodTemplateSchema
from cartography.util import timeit


def _persistent_mount(template: dict[str, Any]) -> dict[str, Any]:
    mounts = template.get("mounts") or {}
    persistent = mounts.get("persistent") if isinstance(mounts, dict) else {}
    return persistent if isinstance(persistent, dict) else {}


def _registry_id(template: dict[str, Any]) -> Any:
    registry = template.get("registry")
    if isinstance(registry, dict):
        return registry.get("id")
    return template.get("containerRegistryId") or template.get("registryId") or registry


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/templates", ("templates", "data"))


def transform(templates: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed = []
    for template in templates:
        persistent_mount = _persistent_mount(template)
        volume_in_gb = first_not_none(template, "volumeInGb", "volume")
        if volume_in_gb is None:
            volume_in_gb = persistent_mount.get("size")
        transformed.append(
            {
                "id": require_non_empty(template.get("id"), "template id"),
                "account_id": account_id,
                "name": template.get("name"),
                "image_name": template.get("imageName") or template.get("image"),
                "container_disk_in_gb": first_not_none(
                    template, "containerDiskInGb", "containerDisk", "disk"
                ),
                "volume_in_gb": volume_in_gb,
                "volume_mount_path": template.get("volumeMountPath")
                or persistent_mount.get("path"),
                "registry_id": _registry_id(template),
                "is_public": first_present(template, "isPublic", "public"),
                "is_serverless": first_present(template, "isServerless", "serverless"),
                "category": template.get("category"),
                "start_ssh": template.get("startSsh"),
                "start_jupyter": template.get("startJupyter"),
                "ports": _port_summaries(template.get("ports")),
            }
        )
    return transformed


@timeit
def load_templates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodTemplateSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodTemplateSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    templates = get(session, base_url)
    transformed = transform(templates, account_id)
    load_templates(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
