import logging
from typing import Any

import neo4j
import scaleway
from scaleway.webhosting.v1 import HostingSummary
from scaleway.webhosting.v1 import WebhostingV1HostingAPI

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.webhosting.hosting import ScalewayWebHostingSchema
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
    hostings = get(client, org_id)
    hostings_by_project = transform_hostings(hostings)
    load_hostings(neo4j_session, hostings_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[HostingSummary]:
    api = WebhostingV1HostingAPI(client)
    return list_all_regions(api.list_hostings_all, organization_id=org_id)


def transform_hostings(
    hostings: list[HostingSummary],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for hosting in hostings:
        formatted = scaleway_obj_to_dict(hosting)

        result.setdefault(hosting.project_id, []).append(formatted)
    return result


@timeit
def load_hostings(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, hostings in data.items():
        logger.info(
            "Loading %d Scaleway Web Hosting accounts in project '%s' into Neo4j.",
            len(hostings),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayWebHostingSchema(),
            hostings,
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
            ScalewayWebHostingSchema(), scoped_job_parameters
        ).run(neo4j_session)
