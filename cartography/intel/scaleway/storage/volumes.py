import logging
from typing import Any

import neo4j
import scaleway
from scaleway.instance.v1 import InstanceV1API
from scaleway.instance.v1 import Volume

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.storage.volume import ScalewayVolumeSchema
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
    volumes = get(client, org_id)
    volumes_by_project = transform_volumes(volumes)
    load_volumes(neo4j_session, volumes_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Volume]:
    api = InstanceV1API(client)
    return api.list_volumes_all(organization=org_id, zone=DEFAULT_ZONE)


def transform_volumes(volumes: list[Volume]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for volume in volumes:
        project_id = volume.project
        formatted_volume = scaleway_obj_to_dict(volume)
        result.setdefault(project_id, []).append(formatted_volume)
    return result


@timeit
def load_volumes(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, volumes in data.items():
        logger.info(
            "Loading %d Scaleway InstanceVolumes in project '%s' into Neo4j.",
            len(volumes),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayVolumeSchema(),
            volumes,
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
        GraphJob.from_node_schema(ScalewayVolumeSchema(), scoped_job_parameters).run(
            neo4j_session
        )
