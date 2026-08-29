import logging
from typing import Any

import neo4j
import scaleway
from scaleway.ipam.v1 import IP
from scaleway.ipam.v1 import IpamV1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.network.ip import ScalewayIPSchema
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
    ips = get(client, org_id)
    ips_by_project = transform_ips(ips)
    load_ips(neo4j_session, ips_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[IP]:
    api = IpamV1API(client)
    return list_all_regions(api.list_i_ps_all, organization_id=org_id)


def transform_ips(ips: list[IP]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for ip in ips:
        formatted_ip = scaleway_obj_to_dict(ip)
        # Flatten the subnet id for the relationship matcher.
        formatted_ip["subnet_id"] = (formatted_ip.get("source") or {}).get("subnet_id")
        result.setdefault(ip.project_id, []).append(formatted_ip)
    return result


@timeit
def load_ips(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, ips in data.items():
        logger.info(
            "Loading %d Scaleway IPs in project '%s' into Neo4j.",
            len(ips),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayIPSchema(),
            ips,
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
        GraphJob.from_node_schema(ScalewayIPSchema(), scoped_job_parameters).run(
            neo4j_session
        )
