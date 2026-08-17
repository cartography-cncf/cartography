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
    hostings_by_project = transform_hostings(hostings, projects_id)
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
    projects_id: list[str],
) -> dict[str, list[dict[str, Any]]]:
    # `ListHostings` is scoped to the organization while cleanup is scoped to the
    # projects returned by the project sync. Keeping the load scope inside the
    # cleanup scope guarantees that every node we write is reachable by a scoped
    # cleanup: a hosting attached to an unknown project would get no RESOURCE edge
    # to a ScalewayProject, and the generated cleanup traverses that edge, so it
    # would linger as a stale node forever.
    known_projects = set(projects_id)
    result: dict[str, list[dict[str, Any]]] = {}
    for hosting in hostings:
        if hosting.project_id not in known_projects:
            logger.warning(
                "Skipping Scaleway Web Hosting account '%s': its project '%s' is not "
                "part of the synced organization projects.",
                hosting.id,
                hosting.project_id,
            )
            continue
        result.setdefault(hosting.project_id, []).append(scaleway_obj_to_dict(hosting))
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
