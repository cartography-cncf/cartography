import logging
from typing import Any

import neo4j
import scaleway
from scaleway.account.v3 import AccountV3ProjectAPI
from scaleway.account.v3 import Project

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.organization import ScalewayOrganizationSchema
from cartography.models.scaleway.project import ScalewayProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    update_tag: int,
) -> list[dict]:
    projects = get(client, org_id)
    formatted_projects = transform_projects(projects)
    load_projects(neo4j_session, formatted_projects, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return formatted_projects


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Project]:
    api = AccountV3ProjectAPI(client)
    return api.list_projects_all(organization_id=org_id)


def transform_projects(projects: list[Project]) -> list[dict[str, Any]]:
    formatted_projects = []
    for project in projects:
        formatted_projects.append(scaleway_obj_to_dict(project))
    return formatted_projects


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ScalewayOrganizationSchema(),
        [{"id": org_id}],
        lastupdated=update_tag,
    )
    logger.info("Loading %d Scaleway Projects into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayProjectSchema(), common_job_parameters).run(
        neo4j_session
    )
