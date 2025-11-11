import logging
from typing import Any

import neo4j
from azure.mgmt.network import NetworkManagementClient

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.azure.network_security_group import (
    AzureNetworkSecurityGroupSchema,
)
from cartography.models.azure.subnet import AzureSubnetSchema
from cartography.models.azure.subnet import AzureSubnetToNSGRel
from cartography.models.azure.virtual_network import AzureVirtualNetworkSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    """
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]


@timeit
def get_virtual_networks(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Virtual Networks in a subscription.
    """
    return [vnet.as_dict() for vnet in client.virtual_networks.list_all()]


@timeit
def get_subnets(
    client: NetworkManagementClient, rg_name: str, vnet_name: str
) -> list[dict]:
    """
    Get subnets for a single Virtual Network. This is a transient, per-resource call.
    """
    return [subnet.as_dict() for subnet in client.subnets.list(rg_name, vnet_name)]


@timeit
def get_network_security_groups(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Network Security Groups in a subscription.
    """
    return [nsg.as_dict() for nsg in client.network_security_groups.list_all()]


def transform_virtual_networks(vnets: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for vnet in vnets:
        transformed.append(
            {
                "id": vnet.get("id"),
                "name": vnet.get("name"),
                "location": vnet.get("location"),
                "provisioning_state": vnet.get("properties", {}).get(
                    "provisioning_state"
                ),
            }
        )
    return transformed


def transform_subnets(subnets: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for subnet in subnets:
        nsg_id = None
        network_security_group = subnet.get("network_security_group")
        if network_security_group:
            nsg_id = network_security_group.get("id")

        transformed.append(
            {
                "id": subnet.get("id"),
                "name": subnet.get("name"),
                "address_prefix": subnet.get("properties", {}).get("address_prefix"),
                "nsg_id": nsg_id,
            }
        )
    return transformed


def transform_network_security_groups(nsgs: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for nsg in nsgs:
        transformed.append(
            {
                "id": nsg.get("id"),
                "name": nsg.get("name"),
                "location": nsg.get("location"),
            }
        )
    return transformed


@timeit
def load_virtual_networks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureVirtualNetworkSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_subnets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    vnet_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureSubnetSchema(),
        data,
        lastupdated=update_tag,
        VNET_ID=vnet_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_network_security_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureNetworkSecurityGroupSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_subnet_nsg_relationships(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    vnet_id: str,
    update_tag: int,
) -> None:
    """
    Loads the relationships from Subnets to the Network Security Groups they are associated with.
    """
    load_matchlinks(
        neo4j_session,
        AzureSubnetToNSGRel(),
        data,
        lastupdated=update_tag,
        _sub_resource_id=vnet_id,
        _sub_resource_label="AzureVirtualNetwork",
    )


@timeit
def _sync_virtual_networks(
    neo4j_session: neo4j.Session,
    client: NetworkManagementClient,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    """
    Syncs Virtual Networks and returns the raw vnet list for further processing.
    """
    vnets = get_virtual_networks(client)
    transformed_vnets = transform_virtual_networks(vnets)
    load_virtual_networks(neo4j_session, transformed_vnets, subscription_id, update_tag)
    GraphJob.from_node_schema(AzureVirtualNetworkSchema(), common_job_parameters).run(
        neo4j_session
    )
    return vnets


@timeit
def _sync_network_security_groups(
    neo4j_session: neo4j.Session,
    client: NetworkManagementClient,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs Network Security Groups.
    """
    nsgs = get_network_security_groups(client)
    transformed_nsgs = transform_network_security_groups(nsgs)
    load_network_security_groups(
        neo4j_session, transformed_nsgs, subscription_id, update_tag
    )
    GraphJob.from_node_schema(
        AzureNetworkSecurityGroupSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def _sync_subnets(
    neo4j_session: neo4j.Session,
    client: NetworkManagementClient,
    vnets: list[dict],
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs Subnets and their relationships for a given list of VNets.
    """
    for vnet in vnets:
        vnet_id = vnet["id"]
        rg_name = _get_resource_group_from_id(vnet_id)
        subnets = get_subnets(client, rg_name, vnet["name"])
        transformed_subnets = transform_subnets(subnets)
        load_subnets(
            neo4j_session, transformed_subnets, vnet_id, subscription_id, update_tag
        )

        subnet_nsg_rels = []
        for subnet in transformed_subnets:
            if subnet.get("nsg_id"):
                subnet_nsg_rels.append(
                    {"NODE_ID": subnet["id"], "NSG_ID": subnet["nsg_id"]}
                )

        if subnet_nsg_rels:
            load_subnet_nsg_relationships(
                neo4j_session, subnet_nsg_rels, vnet_id, update_tag
            )

        subnet_cleanup_params = common_job_parameters.copy()
        subnet_cleanup_params["VNET_ID"] = vnet_id
        GraphJob.from_node_schema(AzureSubnetSchema(), subnet_cleanup_params).run(
            neo4j_session
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Networking for subscription {subscription_id}.")
    client = NetworkManagementClient(credentials.credential, subscription_id)

    vnets = _sync_virtual_networks(
        neo4j_session, client, subscription_id, update_tag, common_job_parameters
    )
    _sync_network_security_groups(
        neo4j_session, client, subscription_id, update_tag, common_job_parameters
    )

    if vnets:
        _sync_subnets(
            neo4j_session,
            client,
            vnets,
            subscription_id,
            update_tag,
            common_job_parameters,
        )
