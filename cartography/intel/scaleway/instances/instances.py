import logging
from typing import Any

import neo4j
import scaleway
from scaleway.instance.v1 import InstanceV1API
from scaleway.instance.v1 import Server

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.instance.instance import ScalewayInstanceSchema
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
    instances = get(client, org_id)
    instances_by_project = transform_instances(instances)
    load_instances(neo4j_session, instances_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Server]:
    api = InstanceV1API(client)
    return api.list_servers_all(organization=org_id, zone=DEFAULT_ZONE)


def transform_instances(
    instances: list[Server],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for instance in instances:
        project_id = instance.project
        formatted_instance = scaleway_obj_to_dict(instance)
        formatted_instance["public_ips"] = [
            ip["id"] for ip in formatted_instance.get("public_ips", [])
        ]
        formatted_instance["volumes_id"] = [
            volume["id"] for volume in formatted_instance.get("volumes", {}).values()
        ]
        result.setdefault(project_id, []).append(formatted_instance)
    return result


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in data.items():
        logger.info(
            "Loading %d Scaleway Instance in project '%s' into Neo4j.",
            len(instances),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayInstanceSchema(),
            instances,
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
        scopped_job_parameters = common_job_parameters.copy()
        scopped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(ScalewayInstanceSchema(), scopped_job_parameters).run(
            neo4j_session
        )
