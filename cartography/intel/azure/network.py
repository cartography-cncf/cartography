import ipaddress
import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.network import NetworkManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_networks(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_networks_tx, subscription_id, data_list, update_tag)


def load_networks_subnets(session: neo4j.Session, data_list: List[Dict], subscription_id: str, update_tag: int) -> None:
    session.execute_write(_load_networks_subnets_tx, data_list, subscription_id, update_tag)


def load_network_routetables(
        session: neo4j.Session,
        subscription_id: str,
        data_list: List[Dict],
        update_tag: int,
) -> None:
    session.execute_write(_load_network_routetables_tx, subscription_id, data_list, update_tag)


def load_network_bastion_hosts(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_network_bastion_hosts_tx, subscription_id, data_list, update_tag)


def attach_network_routetables_to_subnet(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_attach_network_routetables_to_subnet_tx, data_list, update_tag)


def attach_network_bastion_hosts_to_subnet(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_attach_network_bastion_hosts_to_subnet_tx, data_list, update_tag)


def load_network_routes(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_network_routes_tx, data_list, update_tag)


def load_network_security_groups(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_network_security_groups_tx, subscription_id, data_list, update_tag)


def load_network_security_rules(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_network_security_rules_tx, data_list, update_tag)


def load_public_ip_addresses(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_public_ip_addresses_tx, subscription_id, data_list, update_tag)


def load_network_interfaces(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_network_interfaces_tx, subscription_id, data_list, update_tag)


def load_load_balancers(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_load_balancers_tx, subscription_id, data_list, update_tag)


def load_backend_address_pools(
    session: neo4j.Session,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_backend_address_pools_tx, data_list, update_tag)


def load_frontend_ip_configurations(
    session: neo4j.Session,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_frontend_ip_configurations_tx, data_list, update_tag)


def create_relationship_between_network_interface_and_load_balancer(
    session: neo4j.Session,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(
        _create_relationship_between_network_interface_and_load_balancer_tx,
        data_list,
        update_tag,
    )


def load_ip_configurations(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_ip_configurations_tx, data_list, update_tag)


def attach_subnet_to_network_interfaces(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_attach_subnet_to_network_interfaces_tx, data_list, update_tag)


def load_public_ip_network_interfaces_relationship(session: neo4j.Session, interface_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_public_ip_network_interfaces_relationship, interface_id, data_list, update_tag)


def attach_public_ip_to_load_balancer(session: neo4j.Session, load_balancer_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_attach_public_ip_to_load_balancer_tx, load_balancer_id, data_list, update_tag)


def _attach_public_ip_to_load_balancer_tx(tx: neo4j.Transaction, load_balancer_id: str, data_list: List[Dict], update_tag: int) -> None:
    attach_ip_lb = """
    UNWIND $ip_list AS public_ip
    MATCH (ip:AzurePublicIPAddress{id: public_ip.public_ip_id})
    WITH ip
    MATCH (lb:AzureNetworkLoadBalancer{id: $load_balancer_id})
    MERGE (lb)-[r:MEMBER_PUBLIC_IP_ADDRESS]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        attach_ip_lb,
        ip_list=data_list,
        load_balancer_id=load_balancer_id,
        update_tag=update_tag,
    )


def attach_public_ip_to_bastion_host(session: neo4j.Session, bastion_host_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_attach_public_ip_to_bastion_host_tx, bastion_host_id, data_list, update_tag)


def load_usages(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_usages_tx, data_list, update_tag)


@timeit
def get_network_client(credentials: Credentials, subscription_id: str) -> NetworkManagementClient:
    client = NetworkManagementClient(credentials, subscription_id)
    return client


@timeit
def get_networks_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        networks_list = list(map(lambda x: x.as_dict(), client.virtual_networks.list_all()))
        network_data = []
        for network in networks_list:
            network['resource_group'] = get_azure_resource_group_name(network.get('id'))
            network['consolelink'] = azure_console_link.get_console_link(
                id=network['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            network['isDefault'] = False  # since in Azure all the VPCs are created by the user and no defaults exist
            if regions is None:
                network_data.append(network)
            else:
                if network.get('location') in regions or network.get('location') == 'global':
                    network_data.append(network)
        return network_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving networks - {e}")
        return []


def _load_networks_tx(tx: neo4j.Transaction, subscription_id: str, networks_list: List[Dict], update_tag: int) -> None:
    ingest_net = """
    UNWIND $networks AS network
    MERGE (n:AzureNetwork{id: network.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = network.type,
    n.location = network.location,
    n.region = network.location,
    n.resourcegroup = network.resource_group
    SET n.lastupdated = $update_tag,
    n.name = network.name,
    n.consolelink = network.consolelink,
    n.resource_guid = network.resource_guid,
    n.provisioning_state=network.provisioning_state,
    n.enable_ddos_protection=network.enable_ddos_protection,
    n.etag=network.etag,
    n.is_default=network.isDefault
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_net,
        networks=networks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for network in networks_list:
        resource_group = get_azure_resource_group_name(network.get('id'))
        _attach_resource_group_networks(tx, network['id'], resource_group, update_tag)


def _attach_resource_group_networks(tx: neo4j.Transaction, network_id: str, resource_group: str, update_tag: int) -> None:
    ingest_net = """
    MATCH (n:AzureNetwork{id: $network_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name:$resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_net,
        network_id=network_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_networks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_cleanup.json', neo4j_session, common_job_parameters)


def sync_networks(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    networks_list = get_networks_list(client, regions, common_job_parameters)

    load_networks(neo4j_session, subscription_id, networks_list, update_tag)
    sync_networks_subnets(neo4j_session, networks_list, client, subscription_id, update_tag, common_job_parameters)
    sync_network_routetables(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_public_ip_addresses(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_network_interfaces(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_network_bastion_hosts(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_usages(neo4j_session, networks_list, client, update_tag, common_job_parameters)
    sync_load_balancer(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    cleanup_networks(neo4j_session, common_job_parameters)


@timeit
def get_networks_subnets_list(networks_list: List[Dict], client: NetworkManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        networks_subnets_list: List[Dict] = []
        for network in networks_list:
            subnets_list = list(
                map(
                    lambda x: x.as_dict(), client.subnets.list(
                        resource_group_name=network['resource_group'], virtual_network_name=network["name"],
                    ),
                ),
            )

            for subnet in subnets_list:
                subnet['resource_group'] = get_azure_resource_group_name(subnet.get('id'))
                subnet['network_id'] = subnet['id'][:subnet['id'].index("/subnets")]
                subnet['type'] = "Microsoft.Network/Subnets"
                subnet['location'] = network.get('location', 'global')
                subnet['network_security_group_id'] = subnet.get('network_security_group', {}).get('id', None)
                subnet['consolelink'] = azure_console_link.get_console_link(
                    id=subnet['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                subnet['isDefault'] = False  # subnets in Azure are created by user and not by default
            networks_subnets_list.extend(subnets_list)
        return networks_subnets_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving subnets - {e}")
        return []


def _load_networks_subnets_tx(
    tx: neo4j.Transaction,
    networks_subnets_list: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    ingest_network_subnet = """
    UNWIND $networks_subnets_list as subnet
    MERGE (n:AzureNetworkSubnet{id: subnet.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = subnet.type
    SET n.name = subnet.name,
    n.lastupdated = $update_tag,
    n.region= subnet.location,
    n.consolelink = subnet.consolelink,
    n.resource_group_name=subnet.resource_group,
    n.private_endpoint_network_policies=subnet.private_endpoint_network_policies,
    n.private_link_service_network_policies=subnet.private_link_service_network_policies,
    n.etag=subnet.etag,
    n.is_default=subnet.isDefault
    WITH n, subnet
    MATCH (s:AzureNetwork{id: subnet.network_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    WITH n, subnet
    MATCH (sg:AzureNetworkSecurityGroup{id: subnet.network_security_group_id})
    MERGE (n)-[sgr:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET sgr.firstseen = timestamp()
    SET sgr.lastupdated = $update_tag
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[rel:RESOURCE]->(n)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_network_subnet,
        networks_subnets_list=networks_subnets_list,
        update_tag=update_tag,
        SUBSCRIPTION_ID=subscription_id,
    )
    for networks_subnet in networks_subnets_list:
        resource_group = get_azure_resource_group_name(networks_subnet.get('id'))
        _attach_resource_group_networks_subnets(tx, networks_subnet['id'], resource_group, update_tag)


def _attach_resource_group_networks_subnets(tx: neo4j.Transaction, network_subnet_id: str, resource_group: str, update_tag: int) -> None:
    ingest_network_subnet = """
    MATCH (n:AzureNetworkSubnet{id: $network_subnet_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[rel:RESOURCE_GROUP]->(rg)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    tx.run(
        ingest_network_subnet,
        network_subnet_id=network_subnet_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_networks_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_subnets_cleanup.json', neo4j_session, common_job_parameters)


def sync_networks_subnets(
    neo4j_session: neo4j.Session, networks_list: List[Dict],
    client: NetworkManagementClient, subscription_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    networks_subnets_list = get_networks_subnets_list(networks_list, client, common_job_parameters)
    load_networks_subnets(neo4j_session, networks_subnets_list, subscription_id, update_tag)
    cleanup_networks_subnets(neo4j_session, common_job_parameters)


def get_network_routetables_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        network_routetables_list = list(map(lambda x: x.as_dict(), client.route_tables.list_all()))
        tables_data = []
        for routetable in network_routetables_list:
            routetable['resource_group'] = get_azure_resource_group_name(routetable.get('id'))
            routetable['consolelink'] = azure_console_link.get_console_link(
                id=routetable['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            routetable['isDefault'] = False
            if regions is None:
                tables_data.append(routetable)
            else:
                if routetable.get('location') in regions or routetable.get('location') == 'global':
                    tables_data.append(routetable)
        return tables_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving routetables - {e}")
        return []


def _load_network_routetables_tx(
    tx: neo4j.Transaction, subscription_id: str, network_routetables_list: List[Dict], update_tag: int,
) -> None:
    ingest_routetables = """
    UNWIND $network_routetables_list AS routetable
    MERGE (n:AzureRouteTable{id: routetable.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = routetable.type,
    n.location = routetable.location,
    n.region = routetable.location,
    n.resourcegroup = routetable.resource_group
    SET n.lastupdated = $update_tag,
    n.name = routetable.name,
    n.consolelink = routetable.consolelink,
    n.etag=routetable.etag,
    n.is_default=routetable.isDefault
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_routetables,
        network_routetables_list=network_routetables_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for network_routetable in network_routetables_list:
        resource_group = get_azure_resource_group_name(network_routetable.get('id'))
        _attach_resource_group_network_routetables(tx, network_routetable['id'], resource_group, update_tag)


def _attach_resource_group_network_routetables(tx: neo4j.Transaction, network_routetable_id: str, resource_group: str, update_tag: int) -> None:
    ingest_routetables = """
    MATCH (n:AzureRouteTable{id: $network_routetable_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_routetables,
        network_routetable_id=network_routetable_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def _load_network_bastion_hosts_tx(
    tx: neo4j.Transaction, subscription_id: str, network_bastion_host_list: List[Dict], update_tag: int,
) -> None:
    ingest_network_bastion_hosts = """
    UNWIND $network_bastion_host_list as bastion_host
        MERGE (n:AzureNetworkBastionHost{id: bastion_host.id})
        ON CREATE SET n.firstseen = timestamp(),
        n.location = bastion_host.location,
        n.region = bastion_host.location,
        n.dns_name = bastion_host.dns_name
        SET n.lastupdated = $update_tag
        WITH n
        MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
        MERGE (owner)-[r:RESOURCE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_network_bastion_hosts,
        network_bastion_host_list=network_bastion_host_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def _attach_network_routetables_to_subnet_tx(
    tx: neo4j.Transaction, network_routetables_list: List[Dict], update_tag: int,
) -> None:
    attach_routetables_subnet = """
    UNWIND $network_routetables_list AS routetable
    MATCH (n:AzureRouteTable{id: routetable.id})
    UNWIND routetable.subnets as subnet
    MATCH (snet:AzureNetworkSubnet{id: subnet.id})
    MERGE (snet)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        attach_routetables_subnet,
        network_routetables_list=network_routetables_list,
        update_tag=update_tag,
    )


def _attach_network_bastion_hosts_to_subnet_tx(
    tx: neo4j.Transaction, network_bastion_host_list: List[Dict], update_tag: int,
) -> None:
    attach_routetables_subnet = """
    UNWIND $network_bastion_host_list AS bastion_host
    MATCH (n:AzureNetworkBastionHost{id: bastion_host.id})
    UNWIND bastion_host.subnets as subnet
    MATCH (snet:AzureNetworkSubnet{id: subnet.id})
    MERGE (snet)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        attach_routetables_subnet,
        network_bastion_host_list=network_bastion_host_list,
        update_tag=update_tag,
    )


def cleanup_network_routetables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_routetables_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_network_bastion_hosts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_bastion_hosts_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_routetables(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    network_routetables_list = get_network_routetables_list(client, regions, common_job_parameters)
    load_network_routetables(neo4j_session, subscription_id, network_routetables_list, update_tag)
    attach_network_routetables_to_subnet(neo4j_session, network_routetables_list, update_tag)
    cleanup_network_routetables(neo4j_session, common_job_parameters)
    sync_network_routes(neo4j_session, network_routetables_list, client, update_tag, common_job_parameters)


def get_network_bastion_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict):
    try:
        network_bastion_host_list = list(map(lambda x: x.as_dict(), client.bastion_hosts.list()))
        data = []
        for bastion_host in network_bastion_host_list:
            bastion_host['public_ip_address'] = []
            bastion_host['subnets'] = []
            for ip_conf in bastion_host.get('ip_configurations', []):
                bastion_host['public_ip_address'].append(
                    {'public_ip_id': ip_conf.get('public_ip_address', {}).get('id', None)},
                )
                bastion_host['subnets'].append(
                    {"subnet_id": ip_conf.get('subnet', {}).get('id', None)},
                )
            bastion_host['consolelink'] = azure_console_link.get_console_link(
                id=bastion_host['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                data.append(bastion_host)
            else:
                if bastion_host.get('location') in regions or bastion_host.get('location') == 'global':
                    data.append(bastion_host)
        return data
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving routetables - {e}")
        return []


def sync_network_bastion_hosts(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    network_bastion_list = get_network_bastion_list(client, regions, common_job_parameters)
    load_network_bastion_hosts(neo4j_session, subscription_id, network_bastion_list, update_tag)
    attach_network_bastion_hosts_to_subnet(neo4j_session, network_bastion_list, update_tag)
    cleanup_network_bastion_hosts(neo4j_session, common_job_parameters)
    for network_bastion in network_bastion_list:
        attach_public_ip_to_bastion_host(
            neo4j_session, network_bastion.get('id'), network_bastion.get('public_ip_address', []), update_tag,
        )


@timeit
def get_network_routes_list(network_routetables_list: List[Dict], client: NetworkManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        network_routes_list: List[Dict] = []
        for routetable in network_routetables_list:
            routes_list = list(
                map(
                    lambda x: x.as_dict(), client.routes.list(
                        resource_group_name=routetable['resource_group'], route_table_name=routetable['name'],
                    ),
                ),
            )

            for route in routes_list:
                route['resource_group'] = get_azure_resource_group_name(route.get('id'))
                route['routetable_id'] = route['id'][:route['id'].index("/routes")]
                route['location'] = routetable.get('location', 'global')
                route['consolelink'] = azure_console_link.get_console_link(
                    id=route['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            network_routes_list.extend(routes_list)
        return network_routes_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving routes - {e}")
        return []


def _load_network_routes_tx(
    tx: neo4j.Transaction,
    network_routes_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_network_route = """
    UNWIND $network_routes_list as route
    MERGE (n:AzureNetworkRoute{id: route.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = route.type
    SET n.name = route.name,
    n.region = route.location,
    n.address_prefix = route.address_prefix,
    n.next_hop_type = route.next_hop_type,
    n.consolelink = route.consolelink,
    n.lastupdated = $azure_update_tag,
    n.etag=route.etag
    WITH n, route
    MATCH (s:AzureRouteTable{id: route.routetable_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    tx.run(
        ingest_network_route,
        network_routes_list=network_routes_list,
        azure_update_tag=update_tag,
    )
    for network_route in network_routes_list:
        resource_group = get_azure_resource_group_name(network_route.get('id'))
        _attach_resource_group_network_routes(tx, network_route['id'], resource_group, update_tag)


def _attach_resource_group_network_routes(tx: neo4j.Transaction, network_routes_id: str, resource_group: str, update_tag: int) -> None:
    ingest_network_route = """
    MATCH (n:AzureNetworkRoute{id: $network_routes_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    tx.run(
        ingest_network_route,
        network_routes_id=network_routes_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


def cleanup_network_routes(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_routes_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_routes(
    neo4j_session: neo4j.Session, network_routetables_list: List[Dict],
    client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_routes_list = get_network_routes_list(network_routetables_list, client, common_job_parameters)
    load_network_routes(neo4j_session, networks_routes_list, update_tag)
    cleanup_network_routes(neo4j_session, common_job_parameters)


def get_network_security_groups_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        network_security_groups_list = list(map(lambda x: x.as_dict(), client.network_security_groups.list_all()))
        group_list = []
        for network in network_security_groups_list:
            network['resource_group'] = get_azure_resource_group_name(network.get('id'))
            network['consolelink'] = azure_console_link.get_console_link(
                id=network['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            network['isDefault'] = False  # SGs are created by users and not created by default
            if regions is None:
                group_list.append(network)
            else:
                if network.get('location') in regions or network.get('location') == 'global':
                    group_list.append(network)
        return group_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network_security_groups - {e}")
        return []


def _load_network_security_groups_tx(
    tx: neo4j.Transaction, subscription_id: str, network_security_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_network = """
    UNWIND $network_security_groups_list AS network
    MERGE (n:AzureNetworkSecurityGroup{id: network.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = network.type,
    n.location = network.location,
    n.region = network.location,
    n.consolelink = network.consolelink,
    n.resourcegroup = network.resource_group
    SET n.lastupdated = $update_tag,
    n.name = network.name,
    n.etag=network.etag,
    n.is_default=network.isDefault
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_network,
        network_security_groups_list=network_security_groups_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for network_security_group in network_security_groups_list:
        resource_group = get_azure_resource_group_name(network_security_group.get('id'))
        _attach_resource_group_network_security_groups(tx, network_security_group['id'], resource_group, update_tag)


def _attach_resource_group_network_security_groups(tx: neo4j.Transaction, network_security_group_id: str, resource_group: str, update_tag: int) -> None:
    ingest_network = """
    MATCH (n:AzureNetworkSecurityGroup{id: $network_security_group_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_network,
        network_security_group_id=network_security_group_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_network_security_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_security_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_security_groups(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    network_security_groups_list = get_network_security_groups_list(client, regions, common_job_parameters)

    load_network_security_groups(neo4j_session, subscription_id, network_security_groups_list, update_tag)
    cleanup_network_security_groups(neo4j_session, common_job_parameters)
    sync_network_security_rules(neo4j_session, network_security_groups_list, client, update_tag, common_job_parameters)


def sync_nat_gateway(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    nat_gateway_list = get_network_nat_gateway(client, regions, common_job_parameters)

    load_network_nat_gateway(neo4j_session, subscription_id, nat_gateway_list, update_tag)
    for nat_gateway in nat_gateway_list:
        load_network_nat_gateway_subnet(session=neo4j_session, nat_gateway_id=nat_gateway.get('id'), nat_subnet_list=nat_gateway.get("subnets", []), update_tag=update_tag)
    cleanup_network_nat_gateway(neo4j_session, common_job_parameters)


@timeit
def get_network_nat_gateway(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        nat_gateways_list = list(map(lambda x: x.as_dict(), client.nat_gateways.list_all()))
        group_list = []
        for network in nat_gateways_list:
            network['resource_group'] = get_azure_resource_group_name(network.get('id'))
            network['consolelink'] = azure_console_link.get_console_link(
                id=network['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                group_list.append(network)
            else:
                if network.get('location') in regions or network.get('location') == 'global':
                    group_list.append(network)
        return group_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving nat gateways list - {e}")
        return []


def _load_network_nat_gateway_tx(
    tx: neo4j.Transaction, subscription_id: str, nat_gateway_list: List[Dict], update_tag: int,
) -> None:
    ingest_network = """
    UNWIND $nat_gateway_list AS network
    MERGE (n:AzureNatGateway{id: network.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = network.type,
    n.location = network.location,
    n.region = network.location,
    n.consolelink = network.consolelink,
    n.resourcegroup = network.resource_group
    SET n.lastupdated = $update_tag,
    n.name = network.name,
    n.id = network.id,
    n.etag=network.etag
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag


    """

    tx.run(
        ingest_network,
        nat_gateway_list=nat_gateway_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for nat_gateway in nat_gateway_list:
        resource_group = get_azure_resource_group_name(nat_gateway.get('id'))
        _attack_resource_group_network_nat_gateway(tx, nat_gateway['id'], resource_group, update_tag)


def _attack_resource_group_network_nat_gateway(tx: neo4j.Transaction, nat_gateway_id: str, resource_group: str, update_tag: int) -> None:
    ingest_network = """
    MATCH (n:AzureNatGateway{id: $nat_gateway_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_network,
        nat_gateway_id=nat_gateway_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def _load_network_nat_subnet_tx(
    tx: neo4j.Transaction, nat_subnet_list: List[Dict], nat_gateway_id: str, update_tag: int,
) -> None:
    ingest_network = """
    UNWIND $nat_subnet_list AS subnet
        MATCH (s:AzureNetworkSubnet{id: subnet.id})
        WITH s
        MATCH (n:AzureNatGateway{id: $nat_gateway_id})
        MERGE (n)-[r:ATTACHED_TO]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag

    """
    tx.run(
        ingest_network,
        nat_subnet_list=nat_subnet_list,
        nat_gateway_id=nat_gateway_id,
        update_tag=update_tag,
    )


def load_network_nat_gateway(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_network_nat_gateway_tx, subscription_id, data_list, update_tag)


def load_network_nat_gateway_subnet(
    session: neo4j.Session,
    nat_gateway_id: str,
    nat_subnet_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_network_nat_subnet_tx, nat_subnet_list, nat_gateway_id, update_tag)


def cleanup_network_nat_gateway(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_nat_gateway_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_network_security_rules_list(
    network_security_groups_list: List[Dict], client: NetworkManagementClient, common_job_parameters: Dict,
) -> List[Dict]:
    try:
        network_security_rules_list: List[Dict] = []
        for security_group in network_security_groups_list:
            security_rules_list = security_group.get('security_rules', [])
            for rule in security_rules_list:
                rule['resource_group'] = get_azure_resource_group_name(rule.get('id'))
                rule['security_group_id'] = rule['id'][:rule['id'].index("/securityRules")]
                rule['location'] = rule.get('location', 'global')
                rule['access'] = rule.get('access', 'Deny')
                rule['source_port_range'] = rule.get('source_port_range', None)
                rule['destination_port_range'] = rule.get('destination_port_range', None)
                rule['source_address_prefix'] = rule.get('source_address_prefix', None)
                rule['protocol'] = rule.get('protocol', None)
                rule['direction'] = rule.get('direction', None)
                rule['destination_port_ranges'] = rule.get(
                    'properties', {},
                ).get('destination_port_ranges', None)
                rule['destination_address_prefix'] = rule.get('destination_address_prefix', None)
                rule['consolelink'] = azure_console_link.get_console_link(
                    id=rule['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            network_security_rules_list.extend(security_rules_list)
        return network_security_rules_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network_security_rules - {e}")
        return []


def _load_network_security_rules_tx(
    tx: neo4j.Transaction,
    network_security_rules_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_network_rule = """
    UNWIND $network_security_rules_list as rule
    MERGE (n:AzureNetworkSecurityRule{id: rule.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.access = rule.access,
    n.source_port_range = rule.source_port_range,
    n.protocol = rule.protocol,
    n.direction = rule.direction,
    n.consolelink = rule.consolelink,
    n.destination_address_prefix = rule.destination_address_prefix,
    n.source_address_prefix = rule.source_address_prefix,
    n.destination_port_ranges = rule.destination_port_ranges,
    n.destination_port_range = rule.destination_port_range,
    n.type = rule.type
    SET n.name = rule.name,
    n.region = rule.location,
    n.lastupdated = $azure_update_tag,
    n.etag = rule.etag
    WITH n, rule
    MATCH (s:AzureNetworkSecurityGroup{id: rule.security_group_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    ingest_range_ipv4 = """
    UNWIND $ranges_list as range
    MERGE (r:IpRange{id: range.range_id})
    ON CREATE SET r.firstseen = timestamp(), r.range = range.range
    SET r.lastupdated = $azure_update_tag
    WITH r, range
    MATCH (rule:AzureNetworkSecurityRule{id: range.rule_id})
    MERGE (rule)<-[rel:MEMBER_OF_NETWORK_SECURITY_RULE]-(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $azure_update_tag
    """

    ingest_range_ipv6 = """
    UNWIND $ranges_list as range
    MERGE (r:Ipv6Range{id: range.range_id})
    ON CREATE SET r.firstseen = timestamp(), r.range = range.range
    SET r.lastupdated = $azure_update_tag
    WITH r, range
    MATCH (rule:AzureNetworkSecurityRule{id: range.rule_id})
    MERGE (rule)<-[rel:MEMBER_OF_NETWORK_SECURITY_RULE]-(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $azure_update_tag
    """

    tx.run(
        ingest_network_rule,
        network_security_rules_list=network_security_rules_list,
        azure_update_tag=update_tag,
    )

    ranges_list_ipv4 = []
    ranges_list_ipv6 = []

    # Helper function to check if a value is an IP address
    def is_ip_address(value: str) -> bool:
        try:
            ipaddress.ip_network(value, strict=False)
            return True
        except ValueError:
            return False

    # Helper function to differentiate between Ipv4 and Ipv6
    def get_ip_version(ip_range: str) -> str:
        if ip_range == "*":
            return "IpRange"
        try:
            ip_obj = ipaddress.ip_network(ip_range, strict=False)
            return "Ipv6Range" if ip_obj.version == 6 else "IpRange"
        except ValueError:
            return "IpRange"

    # Iterate over the security rules and categorize IP ranges
    for rule in network_security_rules_list:
        for ip_range in rule.get("source_address_prefixes", []):
            if is_ip_address(ip_range):  # Only process if it's an IP address
                label = get_ip_version(ip_range)
                range_id = f"AzureNetworkSecurityRule/{rule['id']}/ipRange/{ip_range}"
                range_entry = {
                    "range_id": range_id,
                    "range": ip_range,
                    "rule_id": rule["id"],
                }
                if label == "Ipv6Range":
                    ranges_list_ipv6.append(range_entry)
                else:
                    ranges_list_ipv4.append(range_entry)
            else:
                range_id = f"AzureNetworkSecurityRule/{rule['id']}/ipRange/{ip_range}"
                ranges_list_ipv4.append({
                    "range_id": range_id,
                    "range": ip_range,
                    "rule_id": rule["id"],
                })

        # Handled the case where, if the list is not present then just take the single IP
        if not rule.get("source_address_prefixes") and rule.get("source_address_prefix"):
            ip_range = rule.get("source_address_prefix")
            if is_ip_address(ip_range):
                label = get_ip_version(ip_range)
                range_id = f"AzureNetworkSecurityRule/{rule['id']}/ipRange/{ip_range}"
                range_entry = {
                    "range_id": range_id,
                    "range": ip_range,
                    "rule_id": rule["id"],
                }
                if label == "Ipv6Range":
                    ranges_list_ipv6.append(range_entry)
                else:
                    ranges_list_ipv4.append(range_entry)
            else:
                range_id = f"AzureNetworkSecurityRule/{rule['id']}/ipRange/{ip_range}"
                ranges_list_ipv4.append({
                    "range_id": range_id,
                    "range": ip_range,
                    "rule_id": rule["id"],
                })

    # executing queries for ipv4 and ipv6
    if ranges_list_ipv4:
        tx.run(
            ingest_range_ipv4,
            ranges_list=ranges_list_ipv4,
            azure_update_tag=update_tag,
        )

    if ranges_list_ipv6:
        tx.run(
            ingest_range_ipv6,
            ranges_list=ranges_list_ipv6,
            azure_update_tag=update_tag,
        )

    for network_security_rule in network_security_rules_list:
        resource_group = get_azure_resource_group_name(network_security_rule.get('id'))
        _attack_resource_group_network_security_rules(tx, network_security_rule['id'], resource_group, update_tag)


def _attack_resource_group_network_security_rules(tx: neo4j.Transaction, network_security_rule_id: str, resource_group: str, update_tag: int) -> None:
    ingest_network_rule = """
    MATCH (n:AzureNetworkSecurityRule{id: $network_security_rule_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    tx.run(
        ingest_network_rule,
        network_security_rule_id=network_security_rule_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


def cleanup_network_security_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_security_rules_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_security_rules(
    neo4j_session: neo4j.Session, network_security_groups_list: List[Dict],
    client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    network_security_rules_list = get_network_security_rules_list(
        network_security_groups_list, client, common_job_parameters,
    )
    load_network_security_rules(neo4j_session, network_security_rules_list, update_tag)
    cleanup_network_security_rules(neo4j_session, common_job_parameters)


def get_public_ip_addresses_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        public_ip_addresses_list = list(map(lambda x: x.as_dict(), client.public_ip_addresses.list_all()))
        publicip_list = []
        for ip in public_ip_addresses_list:
            ip['consolelink'] = azure_console_link.get_console_link(
                id=ip['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            ip["is_static_ip"] = False
            if ip.get("public_ip_allocation_method") == "Static":
                ip["is_static_ip"] = True
            ip['location'] = ip.get('location', '').replace(" ", "").lower()
            if regions is None:
                publicip_list.append(ip)
            else:
                if ip.get('location') in regions or ip.get('location') == 'global':
                    publicip_list.append(ip)
        return publicip_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving public_ip_addresses - {e}")
        return []


def _load_public_ip_addresses_tx(
    tx: neo4j.Transaction, subscription_id: str, public_ip_addresses_list: List[Dict], update_tag: int,
) -> None:
    ingest_address = """
    UNWIND $public_ip_addresses_list AS address
    MERGE (n:AzurePublicIPAddress{id: address.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.id =address.id,
    n.location = address.location,
    n.region = address.location,
    n.consolelink = address.consolelink,
    n.source='azure',
    n.type='Internal',
    n.resource=address.type,
    n.isPublicFacing = true
    SET n.lastupdated = $update_tag,
    n.name = address.name,
    n.ipAddress = address.ip_address,
    n.publicIpAllocationMethod = address.public_ip_allocation_method,
    n.isStaticIp = address.is_static_ip,
    n.etag=address.etag,
    n.region = address.location
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_address,
        public_ip_addresses_list=public_ip_addresses_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_public_ip_addresses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_public_ip_addresses_cleanup.json', neo4j_session, common_job_parameters)


def sync_public_ip_addresses(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    public_ip_addresses_list = get_public_ip_addresses_list(client, regions, common_job_parameters)
    load_public_ip_addresses(neo4j_session, subscription_id, public_ip_addresses_list, update_tag)
    cleanup_public_ip_addresses(neo4j_session, common_job_parameters)


def get_network_interfaces_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        network_interfaces_list = list(map(lambda x: x.as_dict(), client.network_interfaces.list_all()))
        interfaces_list = []
        for interface in network_interfaces_list:
            interface['resource_group'] = get_azure_resource_group_name(interface.get('id'))
            interface['public_ip_address'] = []
            interface['subnet'] = []
            for conf in interface.get('ip_configurations', []):
                interface['public_ip_address'].append(
                    {'public_ip_id': conf.get('public_ip_address', {}).get('id', None)},
                )
                interface['subnet'].append(
                    {'subnet_id': conf.get('subnet', {}).get('id', None)},
                )

            interface['consolelink'] = azure_console_link.get_console_link(
                id=interface['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                interfaces_list.append(interface)
            else:
                if interface.get('location') in regions or interface.get('location') == 'global':
                    interfaces_list.append(interface)
        return interfaces_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network interface - {e}")
        return []


def get_load_balancers_list(client: NetworkManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        network_load_balancer_list = list(map(lambda x: x.as_dict(), client.load_balancers.list_all()))
        load_balancer_list = []
        for load_balancer in network_load_balancer_list:
            load_balancer['resource_group'] = get_azure_resource_group_name(load_balancer.get('id'))
            load_balancer['public_ip_address'] = []
            for frontend_ip_configuration in load_balancer.get('frontend_ip_configurations', []):
                public_ip_id = frontend_ip_configuration.get('public_ip_address', {}).get('id', None)
                if public_ip_id:
                    load_balancer['public_ip_address'].append(
                        {'public_ip_id': public_ip_id},
                    )
            load_balancer['consolelink'] = azure_console_link.get_console_link(
                id=load_balancer['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                load_balancer_list.append(load_balancer)
            else:
                if load_balancer.get('location') in regions or load_balancer.get('location') == 'global':
                    load_balancer_list.append(load_balancer)
        return load_balancer_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network load balancer - {e}")
        return []


def _load_network_interfaces_tx(
    tx: neo4j.Transaction, subscription_id: str, network_interfaces_list: List[Dict], update_tag: int,
) -> None:
    ingest_interface = """
    UNWIND $network_interfaces_list AS interface
    MERGE (n:AzureNetworkInterface{id: interface.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = interface.type,
    n.location = interface.location,
    n.consolelink = interface.consolelink,
    n.region = interface.location
    SET n.lastupdated = $update_tag,
    n.name = interface.name
    WITH n, interface
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    WITH n, interface
    MATCH (sg:AzureNetworkSecurityGroup{id: interface.network_security_group.id})
    MERGE (n)-[sgr:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET sgr.firstseen = timestamp()
    SET sgr.lastupdated = $update_tag
    """

    tx.run(
        ingest_interface,
        network_interfaces_list=network_interfaces_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for network_interface in network_interfaces_list:
        resource_group = get_azure_resource_group_name(network_interface.get('id'))
        _attach_resource_group_network_interfaces(tx, network_interface['id'], resource_group, update_tag)


def _attach_resource_group_network_interfaces(tx: neo4j.Transaction, network_interface_id: str, resource_group: str, update_tag: int) -> None:
    ingest_interface = """
    MATCH (n:AzureNetworkInterface{id: $network_interface_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_interface,
        network_interface_id=network_interface_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def _load_load_balancers_tx(
    tx: neo4j.Transaction, subscription_id: str, load_balancers_list: List[Dict], update_tag: int,
) -> None:
    ingest_load_balancer = """
    UNWIND $load_balancers_list AS lb
    MERGE (n:AzureNetworkLoadBalancer{id: lb.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = lb.type,
    n.location = lb.location,
    n.consolelink = lb.consolelink,
    n.region = lb.location
    SET n.lastupdated = $update_tag,
    n.name = lb.name
    WITH n
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_load_balancer,
        load_balancers_list=load_balancers_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for load_balancer in load_balancers_list:
        resource_group = get_azure_resource_group_name(load_balancer.get('id'))
        _attach_resource_group_load_balancers(tx, load_balancer['id'], resource_group, update_tag)


def _attach_resource_group_load_balancers(tx: neo4j.Transaction, load_balancer_id: str, resource_group: str, update_tag: int) -> None:
    ingest_load_balancer = """
    MATCH (n:AzureNetworkLoadBalancer{id: $load_balancer_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_load_balancer,
        load_balancer_id=load_balancer_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def _load_frontend_ip_configurations_tx(
    tx: neo4j.Transaction, load_balancers_list: List[Dict], update_tag: int,
) -> None:
    ingest_frontend_ip_configurations = """
    UNWIND $frontend_ip_configurations AS config
        MERGE (fipc:AzureLoadBalancerFrontendIPConfiguration{id: config.id})
        ON CREATE SET fipc.firstseen = timestamp(),
        fipc.type = config.type
        SET fipc.name = config.name,
        fipc.private_ip_address = config.private_ip_address,
        fipc.lastupdated = $update_tag
        WITH fipc,config
        MATCH (lb:AzureNetworkLoadBalancer{id: $load_balancer_id})
        MERGE (lb)-[r:HAS]->(fipc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH fipc,config
        MATCH (pip:AzurePublicIPAddress{id: config.public_ip_address.id})
        MERGE (fipc)-[ri:MEMBER_PUBLIC_IP_ADDRESS]->(pip)
        ON CREATE SET ri.firstseen = timestamp()
        SET ri.lastupdated = $update_tag
    """
    for load_balancer in load_balancers_list:
        tx.run(
            ingest_frontend_ip_configurations,
            frontend_ip_configurations=load_balancer.get('frontend_ip_configurations', []),
            load_balancer_id=load_balancer['id'],
            update_tag=update_tag,
        )


def _load_backend_address_pools_tx(
    tx: neo4j.Transaction, load_balancers_list: List[Dict], update_tag: int,
) -> None:
    ingest_backend_address_pool = """
    UNWIND $load_balancers_list AS lb
        MATCH (n:AzureNetworkLoadBalancer{id: lb.id})
        WITH n, lb
        UNWIND lb.backend_address_pools AS b_pool
            MERGE (bap:AzureLoadBalancerBackendAddressPool{id: b_pool.id})
            ON CREATE SET bap.firstseen = timestamp(),
            bap.type = b_pool.type
            SET bap.name = b_pool.name,
            bap.lastupdated = $update_tag
            WITH n, bap, b_pool
            MERGE (n)-[rel:HAS]->(bap)
            ON CREATE SET rel.firstseen = timestamp()
            SET rel.lastupdated = $update_tag
            WITH b_pool, bap
            UNWIND b_pool.backend_ip_configurations as ip_conf
                MATCH (ipc:AzureNetworkInterfaceIPConfiguration{id: ip_conf.id})
                WITH bap, ipc
                MERGE (bap)-[r:HAS]->(ipc)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_backend_address_pool,
        load_balancers_list=load_balancers_list,
        update_tag=update_tag,
    )


def _create_relationship_between_network_interface_and_load_balancer_tx(
    tx: neo4j.Transaction, load_balancers_list: List[Dict], update_tag: int,
) -> None:
    query = """
    UNWIND $load_balancers_list AS lb
        MATCH (n:AzureNetworkLoadBalancer{id: lb.id})-[:HAS]->(:AzureLoadBalancerBackendAddressPool)-[:HAS]->(:AzureNetworkInterfaceIPConfiguration)<-[:CONTAINS]-(interface:AzureNetworkInterface)
        WITH n, interface
        MERGE (interface)-[r:CONNECTED_TO]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        load_balancers_list=load_balancers_list,
        update_tag=update_tag,
    )


def _load_ip_configurations_tx(
    tx: neo4j.Transaction, network_interfaces_list: List[Dict], update_tag: int,
) -> None:
    query = """
    UNWIND $network_interfaces_list AS interface
    MATCH (n:AzureNetworkInterface{id: interface.id})
    WITH n, interface
    UNWIND interface.ip_configurations AS ip_conf
    MERGE (ipc:AzureNetworkInterfaceIPConfiguration{id: ip_conf.id})
    ON CREATE SET ipc.firstseen = timestamp(),
    ipc.private_ip_address = ip_conf.private_ip_address,
    ipc.private_ip_allocation_method = ip_conf.private_ip_allocation_method,
    ipc.private_ip_address_version = ip_conf.private_ip_address_version
    SET ipc.lastupdated = $update_tag,
    ipc.name = ip_conf.name
    WITH ipc, n
    MERGE (n)-[r:CONTAINS]->(ipc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        network_interfaces_list=network_interfaces_list,
        update_tag=update_tag,
    )


def _attach_subnet_to_network_interfaces_tx(
        tx: neo4j.Transaction, network_interfaces_list: List[Dict], update_tag: int,
) -> None:
    query = """
    UNWIND $network_interfaces_list AS interface
    MATCH (n:AzureNetworkInterface{id: interface.id})
    WITH n, interface
    UNWIND interface.subnet AS snet
    MATCH (s:AzureNetworkSubnet{id: snet.subnet_id})
    MERGE (n)-[r:SUBNET]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        network_interfaces_list=network_interfaces_list,
        update_tag=update_tag,
    )


def cleanup_network_interfaces(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_interfaces_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_network_ip_configurations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_ip_configurations_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_network_load_balancers(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_load_balancers_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_network_backend_address_pools(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_backend_address_pools_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_network_frontend_ip_configurations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_frontend_ip_configurations_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_interfaces(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    network_interfaces_list = get_network_interfaces_list(client, regions, common_job_parameters)
    load_network_interfaces(neo4j_session, subscription_id, network_interfaces_list, update_tag)
    load_ip_configurations(neo4j_session, network_interfaces_list, update_tag)
    attach_subnet_to_network_interfaces(neo4j_session, network_interfaces_list, update_tag)
    cleanup_network_ip_configurations(neo4j_session, common_job_parameters)
    cleanup_network_interfaces(neo4j_session, common_job_parameters)
    for interface in network_interfaces_list:
        load_public_ip_network_interfaces_relationship(
            neo4j_session, interface.get(
                'id',
            ), interface.get('public_ip_address', []), update_tag,
        )


def sync_load_balancer(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    load_balancers_list = get_load_balancers_list(client, regions, common_job_parameters)
    load_load_balancers(neo4j_session, subscription_id, load_balancers_list, update_tag)
    load_backend_address_pools(neo4j_session, load_balancers_list, update_tag)
    load_frontend_ip_configurations(neo4j_session, load_balancers_list, update_tag)
    cleanup_network_backend_address_pools(neo4j_session, common_job_parameters)
    cleanup_network_frontend_ip_configurations(neo4j_session, common_job_parameters)
    cleanup_network_load_balancers(neo4j_session, common_job_parameters)
    create_relationship_between_network_interface_and_load_balancer(neo4j_session, load_balancers_list, update_tag)


def _attach_public_ip_to_bastion_host_tx(tx: neo4j.Transaction, bastion_host_id: str, data_list: List[Dict], update_tag: int) -> None:
    attach_ip_bh = """
    UNWIND $ip_list AS public_ip
    MATCH (ip:AzurePublicIPAddress{id: public_ip.public_ip_id})
    WITH ip
    MATCH (bh:AzureNetworkBastionHost{id: $bastion_host_id})
    MERGE (bh)-[r:MEMBER_PUBLIC_IP_ADDRESS]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        attach_ip_bh,
        ip_list=data_list,
        bastion_host_id=bastion_host_id,
        update_tag=update_tag,
    )


def _load_public_ip_network_interfaces_relationship(tx: neo4j.Transaction, interface_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_ip_ni = """
    UNWIND $ip_list AS public_ip
    MATCH (ip:AzurePublicIPAddress{id: public_ip.public_ip_id})
    WITH ip
    MATCH (i:AzureNetworkInterface{id: $interface_id})
    MERGE (i)-[r:MEMBER_PUBLIC_IP_ADDRESS]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_ip_ni,
        ip_list=data_list,
        interface_id=interface_id,
        update_tag=update_tag,
    )


@timeit
def get_usages_list(network: Dict, client: NetworkManagementClient) -> List[Dict]:
    try:
        usages = list(
            map(
                lambda x: x.as_dict(), client.virtual_networks.list_usage(
                    resource_group_name=network['resource_group'], virtual_network_name=network['name'],
                ),
            ),
        )
        return usages
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving usages - {e}")
        return []


def transform_usages(usages: List[Dict], network: Dict, common_job_parameters: Dict) -> List[Dict]:
    usages_list: List[Dict] = []
    for usage in usages:
        usage['network_id'] = usage['id'][:usage['id'].index("/subnets")]
        usage['consolelink'] = azure_console_link.get_console_link(id=usage['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
        usage['location'] = network.get('location', 'global')
    usages_list.extend(usages)

    return usages_list


def _load_usages_tx(
    tx: neo4j.Transaction,
    usages_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_usages = """
    UNWIND $usages_list as usage
    MERGE (n:AzureNetworkUsage{id: usage.id})
    ON CREATE SET n.firstseen = timestamp()
    SET n.currentValue = usage.currentValue,
    n.region= usage.location,
    n.consolelink = usage.consolelink,
    n.lastupdated = $azure_update_tag,
    n.limit=usage.limit,
    n.unit=usage.unit
    WITH n, usage
    MATCH (s:AzureNetwork{id: usage.network_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    tx.run(
        ingest_usages,
        location="global",
        usages_list=usages_list,
        azure_update_tag=update_tag,
    )
    for usages in usages_list:
        resource_group = get_azure_resource_group_name(usages.get('id'))
        _attach_resource_network_usages(tx, usages['id'], resource_group, update_tag)


def _attach_resource_network_usages(tx: neo4j.Transaction, usages_id: str, resource_group: str, update_tag: int) -> None:
    ingest_usages = """
    MATCH (n:AzureNetworkUsage{id: $usages_id})
    WITH n
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (n)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    tx.run(
        ingest_usages,
        usages_id=usages_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


def cleanup_usages(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_usages_cleanup.json', neo4j_session, common_job_parameters)


def sync_usages(
    neo4j_session: neo4j.Session, networks_list: List[Dict], client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for network in networks_list:
        usages = get_usages_list(network, client)
        networks_usages_list = transform_usages(usages, network, common_job_parameters)
        load_usages(neo4j_session, networks_usages_list, update_tag)

    cleanup_usages(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    logger.info("Syncing networks for subscription '%s'.", subscription_id)

    client = get_network_client(credentials, subscription_id)
    sync_network_security_groups(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_networks(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_load_balancer(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
    sync_nat_gateway(neo4j_session, client, subscription_id, update_tag, common_job_parameters, regions)
