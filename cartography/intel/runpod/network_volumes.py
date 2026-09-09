from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.network_volume import RunPodNetworkVolumeSchema
from cartography.util import timeit


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/network-volumes", ("networkVolumes", "data"))


def transform(volumes: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(volume.get("id"), "network volume id"),
            "account_id": account_id,
            "name": volume.get("name"),
            "size": volume.get("size"),
            "volume_type": volume.get("type"),
            "data_center_id": volume.get("dataCenterId") or volume.get("dataCenter"),
            "created_at": volume.get("createdAt"),
        }
        for volume in volumes
    ]


@timeit
def load_network_volumes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodNetworkVolumeSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodNetworkVolumeSchema(), common_job_parameters).run(
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
    volumes = get(session, base_url)
    transformed = transform(volumes, account_id)
    load_network_volumes(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
