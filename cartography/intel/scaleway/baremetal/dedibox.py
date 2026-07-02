import logging
from typing import Any

import neo4j
import scaleway
from scaleway.dedibox.v1 import DediboxV1API
from scaleway.dedibox.v1 import ServerSummary
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_zones
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.baremetal.dedibox import ScalewayDediboxServerSchema
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
    # Only clean up projects we could actually read. A project whose Dedibox
    # API answered "permission denied" is skipped entirely, so its previously
    # ingested nodes are not wiped by a cleanup that saw zero servers.
    fetched_projects: list[str] = []
    for project_id in projects_id:
        servers = get(client, project_id)
        if servers is None:
            continue
        formatted_servers = transform_servers(servers)
        load_servers(neo4j_session, formatted_servers, project_id, update_tag)
        fetched_projects.append(project_id)
    cleanup(neo4j_session, fetched_projects, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    project_id: str,
) -> list[ServerSummary] | None:
    """Return the project's Dedibox servers, or None if the project cannot be
    read (permission denied). None signals the caller to skip load/cleanup for
    that project rather than treating the error as an authoritative empty set."""
    api = DediboxV1API(client)
    # Dedibox has no organization-wide list; it is scoped per project.
    try:
        return list_all_zones(api.list_servers_all, project_id=project_id)
    except ScalewayException as exc:
        # Dedibox is a legacy, opt-in product; accounts that never subscribed to
        # it answer "permissions_denied" for the whole API. Skip rather than
        # aborting the sync or wiping existing inventory.
        if exc.status_code == 403:
            logger.info(
                "Scaleway Dedibox not enabled for project %s, skipping.",
                project_id,
            )
            return None
        raise


def transform_servers(servers: list[ServerSummary]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for server in servers:
        formatted = scaleway_obj_to_dict(server)
        # id is a numeric identifier in the Dedibox API; the graph node id must
        # be a string.
        formatted["id"] = str(formatted["id"])
        formatted["ips"] = [
            ip["address"]
            for interface in (formatted.get("interfaces") or [])
            for ip in (interface.get("ips") or [])
            if ip.get("address")
        ]
        formatted["public_ip"] = formatted["ips"][0] if formatted["ips"] else None
        result.append(formatted)
    return result


@timeit
def load_servers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ScalewayDediboxServerSchema(),
        data,
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
            ScalewayDediboxServerSchema(), scopped_job_parameters
        ).run(neo4j_session)
