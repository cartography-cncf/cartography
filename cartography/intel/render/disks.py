import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.disk import RenderDiskSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/disks",
        "disk",
        params={"ownerId": [owner_id]},
    )


def transform(disks: list[dict[str, Any]], owner_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(disk.get("id"), "disk id"),
            "name": disk.get("name"),
            "ownerId": owner_id,
            "serviceId": disk.get("serviceId"),
            "sizeGB": disk.get("sizeGB"),
            "mountPath": disk.get("mountPath"),
            "createdAt": disk.get("createdAt"),
            "updatedAt": disk.get("updatedAt"),
        }
        for disk in disks
    ]


@timeit
def load_disks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderDiskSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderDiskSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    run_cleanup: bool = True,
) -> list[str]:
    """
    Sync the disks belonging to a single Render workspace.

    :param run_cleanup: Pass False to defer this resource's cleanup to a later,
        explicit `cleanup()` call - used because snapshots are fetched per-disk-id
        after this call returns, so that if one of those per-disk fetches fails
        partway through, this resource's stale disks haven't already been deleted this
        run (which would otherwise leave that failed resource's own still-valid
        snapshot nodes pointing at a disk that no longer exists).
    :return: The synced disk ids, so the caller can fetch their snapshots.
    """
    disks = get(session, owner_id)
    transformed = transform(disks, owner_id)
    load_disks(neo4j_session, transformed, owner_id, update_tag)
    if run_cleanup:
        cleanup(neo4j_session, common_job_parameters)
    return [disk["id"] for disk in transformed]
