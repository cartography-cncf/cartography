import logging
from typing import Any

import neo4j
import scaleway
from scaleway.instance.v1 import InstanceV1API
from scaleway.instance.v1 import Snapshot

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.storage.snapshot import ScalewayVolumeSnapshotSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    snapshots = get(client, org_id)
    snapshots_by_project = transform_snapshots(snapshots)
    load_snapshots(neo4j_session, snapshots_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Snapshot]:
    api = InstanceV1API(client)
    return api.list_snapshots_all(organization=org_id, zone=DEFAULT_ZONE)


def transform_snapshots(
    snapshots: list[Snapshot],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for snapshot in snapshots:
        project_id = snapshot.project
        formatted_snapshot = scaleway_obj_to_dict(snapshot)
        result.setdefault(project_id, []).append(formatted_snapshot)
    return result


@timeit
def load_snapshots(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, snapshots in data.items():
        logger.info(
            "Loading %d Scaleway InstanceSnapshots in project '%s' into Neo4j.",
            len(snapshots),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayVolumeSnapshotSchema(),
            snapshots,
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
            ScalewayVolumeSnapshotSchema(), scoped_job_parameters
        ).run(neo4j_session)
