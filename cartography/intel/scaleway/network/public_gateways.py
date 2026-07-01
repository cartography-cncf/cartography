import logging
from typing import Any

import neo4j
import scaleway
from scaleway.vpcgw.v2 import Gateway
from scaleway.vpcgw.v2 import PatRule
from scaleway.vpcgw.v2 import VpcgwV2API
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_REGIONS
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.network.pat_rule import (
    ScalewayPublicGatewayPatRuleSchema,
)
from cartography.models.scaleway.network.public_gateway import (
    ScalewayPublicGatewaySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Public Gateways are zone-scoped and Scaleway exposes up to three AZs per
# region (e.g. nl-ams-1..3, pl-waw-1..3). We fan out over all three for every
# known region; zones where the service is not deployed answer "unknown
# service" and are skipped, so unsupported permutations are harmless.
_GATEWAY_ZONES = tuple(
    f"{region}-{az}" for region in DEFAULT_REGIONS for az in (1, 2, 3)
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    gateways, pat_rules = get(client, org_id)
    gateways_by_project, pat_rules_by_project = transform(gateways, pat_rules)
    load_gateways(neo4j_session, gateways_by_project, pat_rules_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[Gateway], list[PatRule]]:
    api = VpcgwV2API(client)
    gateways: list[Gateway] = []
    pat_rules: list[PatRule] = []
    for zone in _GATEWAY_ZONES:
        try:
            gateways.extend(api.list_gateways_all(zone=zone, organization_id=org_id))
            pat_rules.extend(api.list_pat_rules_all(zone=zone))
        except ScalewayException as exc:
            if "unknown service" in str(exc).lower():
                logger.info(
                    "Scaleway Public Gateway not available in zone %s, skipping.",
                    zone,
                )
                continue
            raise
    return gateways, pat_rules


def transform(
    gateways: list[Gateway],
    pat_rules: list[PatRule],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    gateways_by_project: dict[str, list[dict[str, Any]]] = {}
    pat_rules_by_project: dict[str, list[dict[str, Any]]] = {}

    # PAT rules inherit the project of their parent gateway: the API does not
    # return project_id on them.
    project_by_gateway_id = {gw.id: gw.project_id for gw in gateways}

    for gateway in gateways:
        formatted = scaleway_obj_to_dict(gateway)
        ipv4 = formatted.get("ipv4") or {}
        formatted["ipv4_address"] = ipv4.get("address")
        # NAT / egress edges: one gateway can front several private networks.
        formatted["private_network_ids"] = [
            gn["private_network_id"]
            for gn in (formatted.get("gateway_networks") or [])
            if gn.get("private_network_id")
        ] or None
        gateways_by_project.setdefault(gateway.project_id, []).append(formatted)

    for pat_rule in pat_rules:
        project_id = project_by_gateway_id.get(pat_rule.gateway_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway PAT rule %s: unknown parent gateway %s.",
                pat_rule.id,
                pat_rule.gateway_id,
            )
            continue
        pat_rules_by_project.setdefault(project_id, []).append(
            scaleway_obj_to_dict(pat_rule)
        )

    return gateways_by_project, pat_rules_by_project


@timeit
def load_gateways(
    neo4j_session: neo4j.Session,
    gateways_by_project: dict[str, list[dict[str, Any]]],
    pat_rules_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, gateways in gateways_by_project.items():
        logger.info(
            "Loading %d Scaleway Public Gateways in project '%s' into Neo4j.",
            len(gateways),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayPublicGatewaySchema(),
            gateways,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
    for project_id, pat_rules in pat_rules_by_project.items():
        load(
            neo4j_session,
            ScalewayPublicGatewayPatRuleSchema(),
            pat_rules,
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
        # Children before parent: PatRule -> PublicGateway.
        GraphJob.from_node_schema(
            ScalewayPublicGatewayPatRuleSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayPublicGatewaySchema(), scoped_job_parameters
        ).run(neo4j_session)
