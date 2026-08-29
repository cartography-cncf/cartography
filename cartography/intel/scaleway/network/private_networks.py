import logging
from typing import Any

import neo4j
import scaleway
from scaleway.vpc.v2 import PrivateNetwork
from scaleway.vpc.v2 import VpcV2API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.network.private_network import (
    ScalewayPrivateNetworkSchema,
)
from cartography.models.scaleway.network.subnet import ScalewaySubnetSchema
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
    private_networks = get(client, org_id)
    networks_by_project, subnets_by_project = transform_private_networks(
        private_networks
    )
    load_private_networks(
        neo4j_session, networks_by_project, subnets_by_project, update_tag
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[PrivateNetwork]:
    api = VpcV2API(client)
    return list_all_regions(api.list_private_networks_all, organization_id=org_id)


def transform_private_networks(
    private_networks: list[PrivateNetwork],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    networks_by_project: dict[str, list[dict[str, Any]]] = {}
    subnets_by_project: dict[str, list[dict[str, Any]]] = {}
    for network in private_networks:
        formatted_network = scaleway_obj_to_dict(network)
        networks_by_project.setdefault(network.project_id, []).append(formatted_network)
        # Subnets are embedded in the private network payload; no extra call.
        for subnet in formatted_network.get("subnets") or []:
            subnets_by_project.setdefault(network.project_id, []).append(subnet)
    return networks_by_project, subnets_by_project


@timeit
def load_private_networks(
    neo4j_session: neo4j.Session,
    networks_by_project: dict[str, list[dict[str, Any]]],
    subnets_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, networks in networks_by_project.items():
        logger.info(
            "Loading %d Scaleway PrivateNetworks in project '%s' into Neo4j.",
            len(networks),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayPrivateNetworkSchema(),
            networks,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )

    for project_id, subnets in subnets_by_project.items():
        load(
            neo4j_session,
            ScalewaySubnetSchema(),
            subnets,
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
        # Clean up children (subnets) before the parent (private network).
        GraphJob.from_node_schema(ScalewaySubnetSchema(), scoped_job_parameters).run(
            neo4j_session
        )
        GraphJob.from_node_schema(
            ScalewayPrivateNetworkSchema(), scoped_job_parameters
        ).run(neo4j_session)
