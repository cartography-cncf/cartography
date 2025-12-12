import logging
from typing import Any

import neo4j
import scaleway
from scaleway.instance.v1 import InstanceV1API
from scaleway.instance.v1 import Ip

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.instance.flexibleip import ScalewayFlexibleIpSchema
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
    flexibleips = get(client, org_id)
    flexibleips_by_project = transform_flexibleips(flexibleips)
    load_flexibleips(neo4j_session, flexibleips_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Ip]:
    api = InstanceV1API(client)
    return api.list_ips_all(organization=org_id, zone=DEFAULT_ZONE)


def transform_flexibleips(
    flexibleips: list[Ip],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for flexibleip in flexibleips:
        project_id = flexibleip.project
        formatted_flexibleip = scaleway_obj_to_dict(flexibleip)
        result.setdefault(project_id, []).append(formatted_flexibleip)
    return result


@timeit
def load_flexibleips(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, flexibleips in data.items():
        logger.info(
            "Loading %d Scaleway Flexible IPs in project '%s' into Neo4j.",
            len(flexibleips),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayFlexibleIpSchema(),
            flexibleips,
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
        GraphJob.from_node_schema(
            ScalewayFlexibleIpSchema(), scopped_job_parameters
        ).run(neo4j_session)
