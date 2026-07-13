import logging
from typing import Any

import neo4j
import scaleway
from scaleway.baremetal.v1 import BaremetalV1API
from scaleway.baremetal.v1 import Server

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_zones
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.baremetal.elastic_metal import (
    ScalewayElasticMetalServerSchema,
)
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
    servers = get(client, org_id)
    servers_by_project = transform_servers(servers)
    load_servers(neo4j_session, servers_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Server]:
    api = BaremetalV1API(client)
    return list_all_zones(api.list_servers_all, organization_id=org_id)


def transform_servers(
    servers: list[Server],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for server in servers:
        formatted = scaleway_obj_to_dict(server)
        formatted["ips"] = [
            ip["address"] for ip in (formatted.get("ips") or []) if ip.get("address")
        ]
        formatted["public_ip"] = formatted["ips"][0] if formatted["ips"] else None
        result.setdefault(server.project_id, []).append(formatted)
    return result


@timeit
def load_servers(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, servers in data.items():
        load(
            neo4j_session,
            ScalewayElasticMetalServerSchema(),
            servers,
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
            ScalewayElasticMetalServerSchema(), scopped_job_parameters
        ).run(neo4j_session)
