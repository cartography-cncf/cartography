import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.infisical import api
from cartography.models.infisical import InfisicalOrganizationSchema
from cartography.models.infisical import InfisicalProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select stable project metadata from the Infisical API response."""
    return [
        {
            "id": project["id"],
            "name": project["name"],
            "slug": project["slug"],
        }
        for project in projects
    ]


def load_projects(
    neo4j_session: neo4j.Session,
    projects: list[dict[str, Any]],
    organization_id: str,
    api_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        InfisicalOrganizationSchema(),
        [{"id": organization_id, "api_url": api_url}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        InfisicalProjectSchema(),
        projects,
        lastupdated=update_tag,
        INFISICAL_ORGANIZATION_ID=organization_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running Infisical project cleanup job")
    GraphJob.from_node_schema(
        InfisicalProjectSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    organization_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Infisical projects for one organization."""
    logger.info("Starting Infisical project sync")
    raw_projects = api.get_projects(session, api_url, organization_id)
    projects = transform(raw_projects)
    load_projects(
        neo4j_session,
        projects,
        organization_id,
        api_url,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Infisical project sync")
