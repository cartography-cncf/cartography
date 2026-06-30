import logging
from typing import Any

import neo4j
import scaleway
from scaleway.vpc.v2 import VPC
from scaleway.vpc.v2 import VpcV2API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.network.vpc import ScalewayVpcSchema
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
    vpcs = get(client, org_id)
    vpcs_by_project = transform_vpcs(vpcs)
    load_vpcs(neo4j_session, vpcs_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[VPC]:
    api = VpcV2API(client)
    return list_all_regions(api.list_vp_cs_all, organization_id=org_id)


def transform_vpcs(vpcs: list[VPC]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for vpc in vpcs:
        formatted_vpc = scaleway_obj_to_dict(vpc)
        result.setdefault(vpc.project_id, []).append(formatted_vpc)
    return result


@timeit
def load_vpcs(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, vpcs in data.items():
        logger.info(
            "Loading %d Scaleway VPCs in project '%s' into Neo4j.",
            len(vpcs),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayVpcSchema(),
            vpcs,
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
        GraphJob.from_node_schema(ScalewayVpcSchema(), scoped_job_parameters).run(
            neo4j_session
        )
