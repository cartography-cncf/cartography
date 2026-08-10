import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import list_resources
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.volume import UnikraftVolumeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return list_resources(session, f"{base_url}/v1/volumes", "volumes")


def transform(volumes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "uuid": require_non_empty(volume.get("uuid"), "volume uuid"),
            "name": volume.get("name"),
            "created_at": volume.get("created_at"),
            "state": volume.get("state"),
            "size_mb": volume.get("size_mb"),
            "persistent": volume.get("persistent"),
            "tags": volume.get("tags"),
            "status": volume.get("status"),
            "message": volume.get("message"),
            "quota_policy": volume.get("quota_policy"),
            "filesystem": volume.get("filesystem"),
            "access_mode": volume.get("access_mode"),
            "mounted_by_instance_ids": [
                mount["uuid"]
                for mount in volume.get("mounted_by") or []
                if mount.get("uuid")
            ],
        }
        for volume in volumes
    ]


@timeit
def load_volumes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    metro: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftVolumeSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        METRO=metro,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftVolumeSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for metro, base_url in METRO_BASE_URLS.items():
        volumes = get(session, base_url)
        transformed = transform(volumes)
        load_volumes(neo4j_session, transformed, account_id, metro, update_tag)
    cleanup(neo4j_session, common_job_parameters)
