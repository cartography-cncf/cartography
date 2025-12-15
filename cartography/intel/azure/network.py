import logging
from typing import Any

import neo4j
from azure.mgmt.network import NetworkManagementClient

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.azure.network_interface import AzureNetworkInterfaceSchema
from cartography.models.azure.network_security_group import (
    AzureNetworkSecurityGroupSchema,
)
from cartography.models.azure.public_ip_address import AzurePublicIPAddressSchema
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


@timeit
def get_public_ip_addresses(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Public IP Addresses in a subscription.
    """
    return [pip.as_dict() for pip in client.public_ip_addresses.list_all()]


@timeit
def get_network_interfaces(client: NetworkManagementClient) -> list[dict]:
    """
    Get a list of all Network Interfaces in a subscription.
    """
    return [interface.as_dict() for interface in client.network_interfaces.list_all()]


def transform_virtual_networks(vnets: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for vnet in vnets:
        # Azure SDK as_dict() may return properties nested or flattened
        provisioning_state = vnet.get("properties", {}).get(
            "provisioning_state"
        ) or vnet.get("provisioning_state")
        transformed.append(
            {
                "id": vnet.get("id"),
                "name": vnet.get("name"),
                "location": vnet.get("location"),
                "provisioning_state": provisioning_state,
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

        # Azure SDK as_dict() may return properties nested or flattened
        address_prefix = subnet.get("properties", {}).get(
            "address_prefix"
        ) or subnet.get("address_prefix")

        transformed.append(
            {
                "id": subnet.get("id"),
                "name": subnet.get("name"),
                "address_prefix": address_prefix,
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


def transform_public_ip_addresses(public_ips: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for public_ip in public_ips:
        # Azure SDK as_dict() may return properties nested or flattened
        properties = public_ip.get("properties", {})
        ip_address = properties.get("ip_address") or public_ip.get("ip_address")
        allocation_method = properties.get(
            "public_ip_allocation_method"
        ) or public_ip.get("public_ip_allocation_method")
        transformed.append(
            {
                "id": public_ip.get("id"),
                "name": public_ip.get("name"),
                "location": public_ip.get("location"),
                "ip_address": ip_address,
                "public_ip_allocation_method": allocation_method,
            }
        )
    return transformed


def transform_network_interfaces(network_interfaces: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for interface in network_interfaces:
        subnet_ids: list[str] = []
        public_ip_ids: list[str] = []
        private_ips: list[str] = []

        for ip_config in interface.get("ip_configurations", []):
            # Azure SDK as_dict() may return properties nested or flattened
            # Try nested first (properties wrapper), then flattened (direct access)
            ip_config_props = ip_config.get("properties", {})

            # Get subnet ID - try nested then flattened
            subnet_ref = ip_config_props.get("subnet") or ip_config.get("subnet")
            if subnet_ref and isinstance(subnet_ref, dict):
                subnet_id = subnet_ref.get("id")
                if subnet_id:
                    subnet_ids.append(subnet_id)

            # Get public IP ID - try nested then flattened
            public_ip_ref = ip_config_props.get("public_ip_address") or ip_config.get(
                "public_ip_address"
            )
            if public_ip_ref and isinstance(public_ip_ref, dict):
                public_ip_id = public_ip_ref.get("id")
                if public_ip_id:
                    public_ip_ids.append(public_ip_id)

            # Get private IP - try nested then flattened
            private_ip = ip_config_props.get("private_ip_address") or ip_config.get(
                "private_ip_address"
            )
            if private_ip:
                private_ips.append(private_ip)

        # Handle case where virtual_machine can be None (unattached NIC)
        vm_ref = interface.get("virtual_machine")
        vm_id = vm_ref.get("id") if vm_ref else None

        transformed.append(
            {
                "id": interface.get("id"),
                "name": interface.get("name"),
                "location": interface.get("location"),
                "mac_address": interface.get("mac_address"),
                "private_ip_addresses": private_ips,
                "VIRTUAL_MACHINE_ID": vm_id,
                "SUBNET_IDS": subnet_ids,
                "PUBLIC_IP_IDS": public_ip_ids,
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
def load_public_ip_addresses(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzurePublicIPAddressSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_network_interfaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureNetworkInterfaceSchema(),
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
def _sync_public_ip_addresses(
    neo4j_session: neo4j.Session,
    client: NetworkManagementClient,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs Public IP Addresses.
    """
    public_ip_addresses = get_public_ip_addresses(client)
    transformed_public_ips = transform_public_ip_addresses(public_ip_addresses)
    load_public_ip_addresses(
        neo4j_session, transformed_public_ips, subscription_id, update_tag
    )
    GraphJob.from_node_schema(AzurePublicIPAddressSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def _sync_network_interfaces(
    neo4j_session: neo4j.Session,
    client: NetworkManagementClient,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs Network Interfaces.
    """
    network_interfaces = get_network_interfaces(client)
    transformed_network_interfaces = transform_network_interfaces(network_interfaces)
    load_network_interfaces(
        neo4j_session, transformed_network_interfaces, subscription_id, update_tag
    )
    GraphJob.from_node_schema(AzureNetworkInterfaceSchema(), common_job_parameters).run(
        neo4j_session
    )


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

    # Subnets must be synced before Network Interfaces so that NIC→Subnet relationships work
    if vnets:
        _sync_subnets(
            neo4j_session,
            client,
            vnets,
            subscription_id,
            update_tag,
            common_job_parameters,
        )

    # Public IPs must be synced before Network Interfaces so that NIC→PublicIP relationships work
    _sync_public_ip_addresses(
        neo4j_session, client, subscription_id, update_tag, common_job_parameters
    )

    _sync_network_interfaces(
        neo4j_session, client, subscription_id, update_tag, common_job_parameters
    )
