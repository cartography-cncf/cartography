import logging
from typing import Any

import neo4j
import scaleway
from scaleway.dedibox.v1 import DediboxV1API
from scaleway.dedibox.v1 import ServerSummary
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
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
    for project_id in projects_id:
        servers = get(client, project_id)
        formatted_servers = transform_servers(servers)
        load_servers(neo4j_session, formatted_servers, project_id, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    project_id: str,
) -> list[ServerSummary]:
    api = DediboxV1API(client)
    # Dedibox has no organization-wide list; it is scoped per project.
    # ponytail: single zone like the Instance module; fan out over zones if
    # multi-zone bare-metal inventory is ever needed.
    try:
        return api.list_servers_all(project_id=project_id, zone=DEFAULT_ZONE)
    except ScalewayException as exc:
        # Dedibox is a legacy, opt-in product; accounts that never subscribed to
        # it answer "permissions_denied" for the whole API. Skip rather than
        # aborting the sync.
        if exc.status_code == 403:
            logger.info(
                "Scaleway Dedibox not enabled for project %s, skipping.",
                project_id,
            )
            return []
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
