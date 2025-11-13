import logging
from typing import Any

import neo4j
from azure.mgmt.network import NetworkManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.load_balancer.load_balancer import AzureLoadBalancerSchema
from cartography.models.azure.load_balancer.load_balancer_backend_pool import (
    AzureLoadBalancerBackendPoolSchema,
)
from cartography.models.azure.load_balancer.load_balancer_frontend_ip import (
    AzureLoadBalancerFrontendIPSchema,
)
from cartography.models.azure.load_balancer.load_balancer_inbound_nat_rule import (
    AzureLoadBalancerInboundNatRuleSchema,
)
from cartography.models.azure.load_balancer.load_balancer_rule import (
    AzureLoadBalancerRuleSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]


@timeit
def get_load_balancers(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Load Balancers in a subscription.
    """
    return [lb.as_dict() for lb in client.load_balancers.list_all()]


def transform_load_balancers(load_balancers: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for lb in load_balancers:
        transformed.append(
            {
                "id": lb.get("id"),
                "name": lb.get("name"),
                "location": lb.get("location"),
                "sku_name": lb.get("sku", {}).get("name"),
            }
        )
    return transformed


def transform_frontend_ips(load_balancer: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for config in load_balancer.get("frontend_ip_configurations", []):
        transformed.append(
            {
                "id": config.get("id"),
                "name": config.get("name"),
                "private_ip_address": config.get("properties", {}).get(
                    "private_ip_address"
                ),
                "public_ip_address_id": config.get("properties", {})
                .get("public_ip_address", {})
                .get("id"),
            }
        )
    return transformed


def transform_backend_pools(load_balancer: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for pool in load_balancer.get("backend_address_pools", []):
        transformed.append(
            {
                "id": pool.get("id"),
                "name": pool.get("name"),
            }
        )
    return transformed


def transform_rules(load_balancer: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for rule in load_balancer.get("load_balancing_rules", []):
        transformed.append(
            {
                "id": rule.get("id"),
                "name": rule.get("name"),
                "protocol": rule.get("properties", {}).get("protocol"),
                "frontend_port": rule.get("properties", {}).get("frontend_port"),
                "backend_port": rule.get("properties", {}).get("backend_port"),
                "FRONTEND_IP_ID": rule.get("frontend_ip_configuration", {}).get("id"),
                "BACKEND_POOL_ID": rule.get("backend_address_pool", {}).get("id"),
            }
        )
    return transformed


def transform_inbound_nat_rules(load_balancer: dict) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for rule in load_balancer.get("inbound_nat_rules", []):
        transformed.append(
            {
                "id": rule.get("id"),
                "name": rule.get("name"),
                "protocol": rule.get("properties", {}).get("protocol"),
                "frontend_port": rule.get("properties", {}).get("frontend_port"),
                "backend_port": rule.get("properties", {}).get("backend_port"),
            }
        )
    return transformed


@timeit
def load_load_balancers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureLoadBalancerSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_frontend_ips(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    lb_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureLoadBalancerFrontendIPSchema(),
        data,
        lastupdated=update_tag,
        LOAD_BALANCER_ID=lb_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_backend_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    lb_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureLoadBalancerBackendPoolSchema(),
        data,
        lastupdated=update_tag,
        LOAD_BALANCER_ID=lb_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    lb_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureLoadBalancerRuleSchema(),
        data,
        lastupdated=update_tag,
        LOAD_BALANCER_ID=lb_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_inbound_nat_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    lb_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureLoadBalancerInboundNatRuleSchema(),
        data,
        lastupdated=update_tag,
        LOAD_BALANCER_ID=lb_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Load Balancers for subscription {subscription_id}.")
    client = NetworkManagementClient(credentials.credential, subscription_id)

    load_balancers = get_load_balancers(client)
    transformed_lbs = transform_load_balancers(load_balancers)
    load_load_balancers(neo4j_session, transformed_lbs, subscription_id, update_tag)

    for lb in load_balancers:
        lb_id = lb["id"]

        frontend_ips = transform_frontend_ips(lb)
        load_frontend_ips(
            neo4j_session, frontend_ips, lb_id, subscription_id, update_tag
        )

        backend_pools = transform_backend_pools(lb)
        load_backend_pools(
            neo4j_session, backend_pools, lb_id, subscription_id, update_tag
        )

        rules = transform_rules(lb)
        load_rules(neo4j_session, rules, lb_id, subscription_id, update_tag)

        inbound_nat_rules = transform_inbound_nat_rules(lb)
        load_inbound_nat_rules(
            neo4j_session, inbound_nat_rules, lb_id, subscription_id, update_tag
        )

        # TODO: Implement relationships from Backend Pools and Inbound NAT Rules to Network Interfaces (NICs).

        # Scoped cleanup for child components
        cleanup_params = common_job_parameters.copy()
        cleanup_params["LOAD_BALANCER_ID"] = lb_id
        GraphJob.from_node_schema(
            AzureLoadBalancerFrontendIPSchema(), cleanup_params
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            AzureLoadBalancerBackendPoolSchema(), cleanup_params
        ).run(neo4j_session)
        GraphJob.from_node_schema(AzureLoadBalancerRuleSchema(), cleanup_params).run(
            neo4j_session
        )
        GraphJob.from_node_schema(
            AzureLoadBalancerInboundNatRuleSchema(), cleanup_params
        ).run(neo4j_session)

    GraphJob.from_node_schema(AzureLoadBalancerSchema(), common_job_parameters).run(
        neo4j_session
    )
