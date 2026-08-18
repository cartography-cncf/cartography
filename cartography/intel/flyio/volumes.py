import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.volume import FlyVolumeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    volumes = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["APP_NAME"],
    )
    transformed = transform(volumes)
    load_volumes(
        neo4j_session,
        transformed,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return transformed


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    app_name: str,
) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/v1/apps/{app_name}/volumes")


def transform(volumes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(volume["id"], "volume id"),
            "name": volume.get("name"),
            "type": volume.get("type"),
            "state": volume.get("state"),
            "size_gb": volume.get("size_gb"),
            "region": volume.get("region"),
            "zone": volume.get("zone"),
            "encrypted": volume.get("encrypted"),
            "attached_machine_id": volume.get("attached_machine_id"),
            "attached_alloc_id": volume.get("attached_alloc_id"),
            "created_at": volume.get("created_at"),
            "blocks": volume.get("blocks"),
            "block_size": volume.get("block_size"),
            "blocks_free": volume.get("blocks_free"),
            "blocks_avail": volume.get("blocks_avail"),
            "bytes_used": volume.get("bytes_used"),
            "bytes_total": volume.get("bytes_total"),
            "fstype": volume.get("fstype"),
            "snapshot_retention": volume.get("snapshot_retention"),
            "auto_backup_enabled": volume.get("auto_backup_enabled"),
            "host_status": volume.get("host_status"),
            "host_dedication_key": volume.get("host_dedication_key"),
        }
        for volume in volumes
    ]


@timeit
def load_volumes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyVolumeSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyVolumeSchema(), common_job_parameters).run(
        neo4j_session,
    )
