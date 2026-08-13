import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_plain_array
from cartography.intel.render.util import require_non_empty
from cartography.models.render.snapshot import RenderSnapshotSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, disk_id: str) -> list[dict[str, Any]]:
    return list_plain_array(session, f"{BASE_URL}/disks/{disk_id}/snapshots")


def transform(
    snapshots: list[dict[str, Any]], disk_id: str, owner_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{disk_id}/{require_non_empty(snapshot.get('createdAt'), 'snapshot createdAt')}",
            "ownerId": owner_id,
            "diskId": disk_id,
            "instanceId": snapshot.get("instanceId"),
            "createdAt": snapshot.get("createdAt"),
        }
        for snapshot in snapshots
    ]


@timeit
def load_snapshots(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderSnapshotSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderSnapshotSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    disk_ids: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_snapshots: list[dict[str, Any]] = []
    for disk_id in disk_ids:
        snapshots = get(session, disk_id)
        all_snapshots.extend(transform(snapshots, disk_id, owner_id))
    load_snapshots(neo4j_session, all_snapshots, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
