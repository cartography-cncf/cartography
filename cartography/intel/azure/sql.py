import ipaddress
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient as MySQLFlexibleServersManagementClient
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient as PostgreSQLFlexibleServersManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sql.models import SecurityAlertPolicyName
from azure.mgmt.sql.models import TransparentDataEncryptionName
from cloudconsolelink.clouds.azure import AzureLinker
from msrestazure.azure_exceptions import CloudError
from netaddr import *

from . import network
from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()

PORT_MAP = {
    "microsoft.sql": 1433,
    "microsoft.dbforpostgresql": 5432,
    "microsoft.dbformysql": 3306,
}


@timeit
def get_client(credentials: Credentials, subscription_id: str) -> SqlManagementClient:
    """
    Getting the Azure SQL client
    """
    client = SqlManagementClient(credentials, subscription_id)
    return client


def _extract_engine_info(server: Dict) -> Tuple[str, str, int]:
    version = server.get('version', '')

    # Determine engine type from the resource ID
    server_id = server.get('id', '').lower()

    # Default values (Azure SQL Database)
    engine = "sqlserver"
    port = 1433

    # Determine engine type from resource provider in the ID
    if 'microsoft.dbforpostgresql' in server_id:
        engine = "postgres"
        port = 5432
    elif 'microsoft.dbformysql' in server_id:
        engine = "mysql"
        port = 3306
    elif 'microsoft.sql' in server_id:
        engine = "sqlserver"
        port = 1433

    # Log the extraction for debugging
    logger.debug(
        f"Extracted engine info for {server.get('name')}: "
        f"engine={engine}, version={version}, port={port}",
    )

    return engine, version, port


def _extract_endpoint_info(
    server: Dict,
    credentials: Credentials,
    subscription_id: str,
) -> Dict:
    endpoint_info = {
        'public_endpoint': None,
    }

    # Public endpoint - fully qualified domain name
    endpoint_info['public_endpoint'] = server.get('fully_qualified_domain_name')

    return endpoint_info


def get_server_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    """
    Returning the list of Azure SQL servers, PostgreSQL servers, and MySQL servers.
    """
    # Gather all server types
    server_list = []
    server_list.extend(_get_sql_database_servers(credentials, subscription_id))
    server_list.extend(_get_postgresql_flexible_servers(credentials, subscription_id))
    server_list.extend(_get_mysql_flexible_servers(credentials, subscription_id))
    server_list.extend(_get_postgresql_rdbms_servers(credentials, subscription_id))
    server_list.extend(_get_mysql_rdbms_servers(credentials, subscription_id))

    # Enrich server data with additional metadata
    server_data = [
        _enrich_server_data(server, credentials, subscription_id, common_job_parameters)
        for server in server_list
    ]

    # Filter by region if specified
    return _filter_servers_by_region(server_data, regions)


def _get_sql_database_servers(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get Azure SQL Database servers.
    """
    try:
        client = get_client(credentials, subscription_id)
        sql_servers = list(map(lambda x: x.as_dict(), client.servers.list()))
        logger.debug(f"Retrieved {len(sql_servers)} SQL Database servers")
        return sql_servers
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving SQL servers - {e}")
    except ResourceNotFoundError as e:
        logger.warning(f"SQL Server resource not found error - {e}")
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving SQL servers - {e}")
    return []


def _get_postgresql_flexible_servers(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get Azure Database for PostgreSQL Flexible Servers.
    """
    try:
        pg_flex_client = PostgreSQLFlexibleServersManagementClient(credentials, subscription_id)
        pg_flex_servers = list(map(lambda x: x.as_dict(), pg_flex_client.servers.list()))
        logger.debug(f"Retrieved {len(pg_flex_servers)} PostgreSQL Flexible Servers")
        return pg_flex_servers
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving PostgreSQL Flexible Servers - {e}")
    except ResourceNotFoundError as e:
        logger.warning(f"PostgreSQL Flexible Server resource not found error - {e}")
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving PostgreSQL Flexible Servers - {e}")
    except Exception as e:
        logger.warning(f"Unexpected error while retrieving PostgreSQL Flexible Servers - {e}")
    return []


def _get_mysql_flexible_servers(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get Azure Database for MySQL Flexible Servers.
    """
    try:
        mysql_flex_client = MySQLFlexibleServersManagementClient(credentials, subscription_id)
        mysql_flex_servers = list(map(lambda x: x.as_dict(), mysql_flex_client.servers.list()))
        logger.debug(f"Retrieved {len(mysql_flex_servers)} MySQL Flexible Servers")
        return mysql_flex_servers
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving MySQL Flexible Servers - {e}")
    except ResourceNotFoundError as e:
        logger.warning(f"MySQL Flexible Server resource not found error - {e}")
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving MySQL Flexible Servers - {e}")
    except Exception as e:
        logger.warning(f"Unexpected error while retrieving MySQL Flexible Servers - {e}")
    return []


def _get_postgresql_rdbms_servers(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get Azure Database for PostgreSQL (Regular RDBMS) servers.
    """
    try:
        pg_rdbms_client = PostgreSQLManagementClient(credentials, subscription_id)
        pg_rdbms_servers = list(map(lambda x: x.as_dict(), pg_rdbms_client.servers.list()))
        logger.debug(f"Retrieved {len(pg_rdbms_servers)} PostgreSQL RDBMS Servers")
        return pg_rdbms_servers
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving PostgreSQL RDBMS Servers - {e}")
    except ResourceNotFoundError as e:
        logger.warning(f"PostgreSQL RDBMS Server resource not found error - {e}")
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving PostgreSQL RDBMS Servers - {e}")
    except Exception as e:
        logger.warning(f"Unexpected error while retrieving PostgreSQL RDBMS Servers - {e}")
    return []


def _get_mysql_rdbms_servers(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get Azure Database for MySQL (Regular RDBMS) servers.
    """
    try:
        mysql_rdbms_client = MySQLManagementClient(credentials, subscription_id)
        mysql_rdbms_servers = list(map(lambda x: x.as_dict(), mysql_rdbms_client.servers.list()))
        logger.debug(f"Retrieved {len(mysql_rdbms_servers)} MySQL RDBMS Servers")
        return mysql_rdbms_servers
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving MySQL RDBMS Servers - {e}")
    except ResourceNotFoundError as e:
        logger.warning(f"MySQL RDBMS Server resource not found error - {e}")
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving MySQL RDBMS Servers - {e}")
    except Exception as e:
        logger.warning(f"Unexpected error while retrieving MySQL RDBMS Servers - {e}")
    return []


def _enrich_server_data(
    server: Dict,
    credentials: Credentials,
    subscription_id: str,
    common_job_parameters: Dict,
) -> Dict:
    """
    Enrich server data with additional metadata.
    """
    server['resourceGroup'] = get_azure_resource_group_name(server.get('id'))
    server['publicNetworkAccess'] = server.get('properties', {}).get('public_network_access', 'Disabled')
    server['consolelink'] = azure_console_link.get_console_link(
        id=server['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
    )

    engine, engine_version, port = _extract_engine_info(server)
    server['engine'] = engine
    server['engineVersion'] = engine_version
    server['port'] = port
    server['location'] = server.get("location", "").replace(" ", "").lower()

    endpoint_info = _extract_endpoint_info(server, credentials, subscription_id)
    server['endpoint'] = endpoint_info['public_endpoint']

    return server


def _filter_servers_by_region(servers: List[Dict], regions: list) -> List[Dict]:
    """
    Filter servers by region if regions list is provided.
    """
    if regions is None:
        return servers
    return [s for s in servers if s.get('location') in regions or s.get('location') == 'global']


@timeit
def load_server_data(
        neo4j_session: neo4j.Session, subscription_id: str, server_list: List[Dict],
        azure_update_tag: int,
) -> None:
    """
    Ingest the server details into neo4j.
    """
    ingest_server = """
    UNWIND $server_list as server
    MERGE (s:AzureSQLServer{id: server.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.resourcegroup = server.resourceGroup,
    s.location = server.location,
    s.region = server.location
    SET s.lastupdated = $azure_update_tag,
    s.name = server.name,
    s.publicNetworkAccess = server.publicNetworkAccess,
    s.consolelink = server.consolelink,
    s.kind = server.kind,
    s.state = server.state,
    s.version = server.version,
    s.engine = server.engine,
    s.engineVersion = server.engineVersion,
    s.endpoint = server.endpoint,
    s.port = server.port
    WITH s
    MATCH (owner:AzureSubscription{id: $AZURE_SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_server,
        server_list=server_list,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )
    for server in server_list:
        resource_group = get_azure_resource_group_name(server.get('id'))
        _attach_resource_group_server(neo4j_session, server.get('id'), resource_group, azure_update_tag)


def _attach_resource_group_server(neo4j_session: neo4j.Session, server_id: str, server_resource_group: str, azure_update_tag: int) -> None:
    ingest_server = """
    MATCH (s:AzureSQLServer{id: $server_id})
    WITH s
    MATCH (rg:AzureResourceGroup{name: $server_resource_group})
    MERGE (s)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_server,
        server_id=server_id,
        server_resource_group=server_resource_group,
        azure_update_tag=azure_update_tag,
    )


def load_server_private_endpoint_connection(neo4j_session: neo4j.Session, server_list: List[Dict], azure_update_tag: int) -> None:
    """
    Ingest & attach server private endpoint connection
    """
    ingest_attach_private_endpoint_connection = """
    MATCH (s:AzureSQLServer{id: $server_id})
    UNWIND $private_endpoint_connections as pec
    MERGE (aspec:AzureServerPrivateEndpointConnection{id: pec.id})
    ON CREATE SET aspec.firstseen = timestamp()
    SET aspec.provisioning_state = pec.properties.provisioning_state,
    aspec.private_endpoint = pec.properties.private_endpoint.id,
    aspec.lastupdated = $azure_update_tag
    MERGE (s)-[r:HAS]->(aspec)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    for server in server_list:
        neo4j_session.run(
            ingest_attach_private_endpoint_connection,
            server_id=server.get('id'),
            private_endpoint_connections=server.get('private_endpoint_connections', []),
            azure_update_tag=azure_update_tag,
        )
        for private_endpoint_connection in server.get('private_endpoint_connections', []):
            resource_group = get_azure_resource_group_name(private_endpoint_connection.get('id'))
            _attach_resource_group_server_private_endpoint_connections(neo4j_session, private_endpoint_connection['id'], resource_group, azure_update_tag)


def _attach_resource_group_server_private_endpoint_connections(neo4j_session: neo4j.Session, private_endpoint_connection_id: str, resource_group: str, azure_update_tag: int) -> None:
    ingest_attach_private_endpoint_connection = """
    MATCH (aspec:AzureServerPrivateEndpointConnection{id: $aspec_id})
    WITH aspec,
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (aspec)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_attach_private_endpoint_connection,
        aspec_id=private_endpoint_connection_id,
        resource_group=resource_group,
        azure_update_tag=azure_update_tag,
    )


@timeit
def sync_server_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        server_list: List[Dict], sync_tag: int, common_job_parameters: Dict,
) -> None:
    details = get_server_details(credentials, subscription_id, server_list)
    load_server_details(neo4j_session, credentials, subscription_id, details, sync_tag, common_job_parameters)


@timeit
def get_server_details(
        credentials: Credentials, subscription_id: str, server_list: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over each servers to get its resource details.
    """
    for server in server_list:
        dns_alias = get_dns_aliases(credentials, subscription_id, server)
        ad_admins = get_ad_admins(credentials, subscription_id, server)
        r_databases = get_recoverable_databases(credentials, subscription_id, server)
        rd_databases = get_restorable_dropped_databases(credentials, subscription_id, server)
        fgs = get_failover_groups(credentials, subscription_id, server)
        elastic_pools = get_elastic_pools(credentials, subscription_id, server)
        databases = get_databases(credentials, subscription_id, server)
        firewall_rules = get_firewall_rules(credentials, subscription_id, server)
        yield server['id'], server['name'], server[
            'resourceGroup'
        ], dns_alias, ad_admins, r_databases, rd_databases, fgs, elastic_pools, databases, firewall_rules


@timeit
def get_dns_aliases(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of the DNS aliases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        dns_aliases = list(
            map(
                lambda x: x.as_dict(),
                client.server_dns_aliases.list_by_server(server['resourceGroup'], server['name']),
            ),
        )
        for aliase in dns_aliases:
            aliase["location"] = server.get("location", "global").replace(" ", "").lower()
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving DNS Aliases - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"DNS Alias resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving Azure Server DNS Aliases - {e}")
        return []

    return dns_aliases


@timeit
def get_ad_admins(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of the Server AD Administrators in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        ad_admins = list(
            map(
                lambda x: x.as_dict(),
                client.server_azure_ad_administrators.list_by_server(
                    server['resourceGroup'],
                    server['name'],
                ),
            ),
        )
        for admin in ad_admins:
            admin["location"] = server.get("location", "global").replace(" ", "").lower()

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving Azure AD Administrators - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Azure AD Administrators resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving server azure AD Administrators - {e}")
        return []

    return ad_admins


@timeit
def get_recoverable_databases(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of the Recoverable databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        recoverable_databases = list(
            map(
                lambda x: x.as_dict(),
                client.recoverable_databases.list_by_server(
                    server['resourceGroup'],
                    server['name'],
                ),
            ),
        )

    except CloudError:
        # The API returns a '404 CloudError: Not Found for url: <url>' if no recoverable databases are present.
        return []
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving recoverable databases - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Recoverable databases resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving recoverable databases - {e}")
        return []

    return recoverable_databases


@timeit
def get_restorable_dropped_databases(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of the Restorable Dropped Databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        restorable_dropped_databases = list(
            map(
                lambda x: x.as_dict(),
                client.restorable_dropped_databases.list_by_server(
                    server['resourceGroup'], server['name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving Restorable Dropped Databases - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Restorable Dropped Databases resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving restorable dropped databases - {e}")
        return []

    return restorable_dropped_databases


@timeit
def get_failover_groups(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of Failover groups in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        failover_groups = list(
            map(lambda x: x.as_dict(), client.failover_groups.list_by_server(server['resourceGroup'], server['name'])),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving Failover groups - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Failover groups resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving failover groups - {e}")
        return []

    return failover_groups


@timeit
def get_elastic_pools(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of Elastic Pools in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        elastic_pools = list(
            map(lambda x: x.as_dict(), client.elastic_pools.list_by_server(server['resourceGroup'], server['name'])),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving Elastic Pools - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Elastic Pools resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving elastic pools - {e}")
        return []

    return elastic_pools


@timeit
def get_databases(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    """
    Returns details of Databases in a SQL server.
    """
    try:
        client = get_client(credentials, subscription_id)
        databases = list(
            map(lambda x: x.as_dict(), client.databases.list_by_server(server['resourceGroup'], server['name'])),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving SQL databases - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"SQL databases resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving databases - {e}")
        return []

    return databases


@timeit
def load_server_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        details: List[Tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionaries for every resource in the server so we can import them in a single query
    """
    dns_aliases = []
    ad_admins = []
    recoverable_databases = []
    restorable_dropped_databases = []
    failover_groups = []
    elastic_pools = []
    databases = []
    fw_rules = []

    for server_id, name, rg, dns_alias, ad_admin, r_database, rd_database, fg, elastic_pool, database, firewall_rules in details:
        if len(dns_alias) > 0:
            for alias in dns_alias:
                alias['server_name'] = name
                alias['server_id'] = server_id
                alias['consolelink'] = azure_console_link.get_console_link(
                    id=alias['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                dns_aliases.append(alias)

        if len(ad_admin) > 0:
            for admin in ad_admin:
                admin['server_name'] = name
                admin['server_id'] = server_id
                admin['consolelink'] = azure_console_link.get_console_link(
                    id=admin['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                ad_admins.append(admin)

        if len(r_database) > 0:
            for rdb in r_database:
                rdb['server_name'] = name
                rdb['server_id'] = server_id
                rdb['consolelink'] = azure_console_link.get_console_link(
                    id=rdb['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                recoverable_databases.append(rdb)

        if len(rd_database) > 0:
            for rddb in rd_database:
                rddb['server_name'] = name
                rddb['server_id'] = server_id
                rddb['consolelink'] = azure_console_link.get_console_link(
                    id=rddb['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                restorable_dropped_databases.append(rddb)

        if len(fg) > 0:
            for group in fg:
                group['server_name'] = name
                group['server_id'] = server_id
                group['consolelink'] = azure_console_link.get_console_link(
                    id=group['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                failover_groups.append(group)

        if len(elastic_pool) > 0:
            for pool in elastic_pool:
                pool['server_name'] = name
                pool['server_id'] = server_id
                pool['consolelink'] = azure_console_link.get_console_link(
                    id=pool['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                elastic_pools.append(pool)

        if len(database) > 0:
            for db in database:
                db['server_name'] = name
                db['server_id'] = server_id
                db['resource_group_name'] = rg
                db['consolelink'] = azure_console_link.get_console_link(
                    id=db['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                databases.append(db)

        if len(firewall_rules) > 0:
            for rules in firewall_rules:
                rules['server_name'] = name
                rules['server_id'] = server_id
                rules['resource_group_name'] = rg
                rules['consolelink'] = ''  # TODO: implement for firewall rules
                fw_rules.append(rules)

    _load_server_dns_aliases(neo4j_session, dns_aliases, update_tag)
    _load_server_ad_admins(neo4j_session, ad_admins, update_tag)
    _load_recoverable_databases(neo4j_session, recoverable_databases, update_tag)
    _load_restorable_dropped_databases(neo4j_session, restorable_dropped_databases, update_tag)
    _load_failover_groups(neo4j_session, failover_groups, update_tag)
    _load_elastic_pools(neo4j_session, elastic_pools, update_tag)
    _load_databases(neo4j_session, databases, update_tag)
    _load_firewall_rules(neo4j_session, fw_rules, update_tag)

    network_client = network.get_network_client(credentials, subscription_id)
    public_ips = [ip.get('ip_address') for ip in network.get_public_ip_addresses_list(network_client, None, common_job_parameters) if ip.get('ip_address')]

    for fw_rule in fw_rules:
        start_ip = fw_rule['start_ip_address']
        end_ip = fw_rule['end_ip_address']
        ip_range = []

        if start_ip == "0.0.0.0":
            if end_ip == "0.0.0.0":
                ip_range = public_ips

            elif end_ip == "255.255.255.255":
                ip_range = public_ips

        if len(ip_range) == 0:
            ip_range = iter_iprange(start_ip, end_ip)

        for ip in ip_range:
            if str(ip) in public_ips:
                attach_firewall_rule_to_public_ip(neo4j_session, fw_rule, str(ip), "Azure", "Internal", update_tag)
            elif not ipaddress.ip_address(str(ip)).is_private:
                attach_firewall_rule_to_public_ip(neo4j_session, fw_rule, str(ip), "Azure", "External", update_tag)

    sync_database_details(neo4j_session, credentials, subscription_id, databases, update_tag, common_job_parameters)


@timeit
def _load_server_dns_aliases(
        neo4j_session: neo4j.Session, dns_aliases: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the DNS Alias details into neo4j.
    """
    ingest_dns_aliases = """
    UNWIND $dns_aliases_list as dns_alias
    MERGE (alias:AzureServerDNSAlias{id: dns_alias.id})
    ON CREATE SET alias.firstseen = timestamp()
    SET alias.name = dns_alias.name,
    alias.location = dns_alias.location,
    alias.region = dns_alias.location,
    alias.consolelink = dns_alias.consolelink,
    alias.dnsrecord = dns_alias.azure_dns_record,
    alias.lastupdated = $azure_update_tag
    WITH alias, dns_alias
    MATCH (s:AzureSQLServer{id: dns_alias.server_id})
    MERGE (s)-[r:USED_BY]->(alias)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_dns_aliases,
        dns_aliases_list=dns_aliases,
        azure_update_tag=update_tag,
    )
    for dns_aliases in dns_aliases:
        resource_group = get_azure_resource_group_name(dns_aliases.get('id'))
        _attach_resource_group_dns_alias(neo4j_session, dns_aliases['id'], resource_group, update_tag)


def _attach_resource_group_dns_alias(neo4j_session: neo4j.Session, dns_alias_id: str, resource_group: str, update_tag: int) -> None:
    ingest_dns_aliases = """
    MATCH (alias:AzureServerDNSAlias{id: $dns_alias_id})
    WITH alias
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (alias)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_dns_aliases,
        dns_alias_id=dns_alias_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_firewall_rules(neo4j_session: neo4j.Session, fw_rules: List[Dict], update_tag: int) -> None:
    """
    Ingest the firewall rules into neo4j.
    """
    ingest_firewall_rules = """
    UNWIND $fw_rules as fw_rule
    MERGE (rule:AzureFirewallRule{id: fw_rule.id})
    ON CREATE SET rule.firstseen = timestamp()
    SET rule.name = fw_rule.name,
    rule.region = fw_rule.location,
    rule.start_ip_address = fw_rule.start_ip_address,
    rule.end_ip_address = fw_rule.end_ip_address,
    rule.lastupdated = $azure_update_tag
    WITH rule, fw_rule
    MATCH (s: AzureSQLServer{id: fw_rule.server_id})
    MERGE (s)-[r:HAS]->(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_firewall_rules,
        fw_rules=fw_rules,
        azure_update_tag=update_tag,
    )
    for fw_rule in fw_rules:
        resource_group = get_azure_resource_group_name(fw_rule.get('id'))
        _attach_resource_group_fw_rule(neo4j_session, fw_rule['id'], resource_group, update_tag)


def _attach_resource_group_fw_rule(neo4j_session: neo4j.Session, fw_rule_id: str, resource_group: str, update_tag: int) -> None:
    ingest_firewall_rules = """
    MATCH (rule:AzureFirewallRule{id: $fw_rule_id})
    WITH rule
    MATCH (rg: AzureResourceGroup{name: $resource_group})
    MERGE (rule)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_firewall_rules,
        fw_rule_id=fw_rule_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


def attach_firewall_rule_to_public_ip(session: neo4j.Session, fw_rule: Dict, public_ip: str, source: str, type: str, update_tag: int) -> None:
    session.execute_write(_attach_firewall_rule_to_public_ip_tx, fw_rule, public_ip, source, type, update_tag)


def _attach_firewall_rule_to_public_ip_tx(tx: neo4j.Transaction, fw_rule: Dict, public_ip: str, source: str, type: str, update_tag: int) -> None:
    ingest_address = """
    MATCH (fwr:AzureFirewallRule{id: $fw_rule})
    WITH fwr
    MERGE (ip:AzurePublicIPAddress{ipAddress: $public_ip})
    ON CREATE SET ip.firstseen = timestamp()
    SET
        ip.id =$public_ip,
        ip.name=$public_ip,
        ip.source =$source,
        ip.type=$type,
        ip.resource=$resource,
        ip.ipAddress=$public_ip
    MERGE (fwr)-[r:MEMBER_PUBLIC_IP_ADDRESS]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_address,
        fw_rule=fw_rule['id'],
        public_ip=public_ip,
        source=source,
        type=type,
        resource=fw_rule['type'],
        update_tag=update_tag,
    )


@timeit
def _load_server_ad_admins(
        neo4j_session: neo4j.Session, ad_admins: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the Server AD Administrators details into neo4j.
    """
    ingest_ad_admins = """
    UNWIND $ad_admins_list as ad_admin
    MERGE (a:AzureServerADAdministrator{id: ad_admin.id})
    ON CREATE SET a.firstseen = timestamp()
    SET a.name = ad_admin.name,
    a.administratortype = ad_admin.administrator_type,
    a.consolelink = ad_admin.consolelink,
    a.login = ad_admin.login,
    a.location = ad_admin.location,
    a.region = ad_admin.location,
    a.lastupdated = $azure_update_tag
    WITH a, ad_admin
    MATCH (s:AzureSQLServer{id: ad_admin.server_id})
    MERGE (s)-[r:ADMINISTERED_BY]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_ad_admins,
        ad_admins_list=ad_admins,
        azure_update_tag=update_tag,
    )
    for ad_admin in ad_admins:
        resource_group = get_azure_resource_group_name(ad_admin.get('id'))
        _attach_resource_group_ad_admin(neo4j_session, ad_admin['id'], resource_group, update_tag)


def _attach_resource_group_ad_admin(neo4j_session: neo4j.Session, ad_admin_id: str, resource_group: str, update_tag: int) -> None:
    ingest_ad_admins = """
    MATCH (a:AzureServerADAdministrator{id: $ad_admin_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_ad_admins,
        ad_admin_id=ad_admin_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_recoverable_databases(
        neo4j_session: neo4j.Session, recoverable_databases: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the recoverable database details into neo4j.
    """
    ingest_recoverable_databases = """
    UNWIND $recoverable_databases_list as rec_db
    MERGE (rd:AzureRecoverableDatabase{id: rec_db.id})
    ON CREATE SET rd.firstseen = timestamp()
    SET rd.name = rec_db.name,
    rd.region = $region,
    rd.edition = rec_db.edition,
    rd.consolelink = rec_db.consolelink,
    rd.servicelevelobjective = rec_db.service_level_objective,
    rd.lastbackupdate = rec_db.last_available_backup_date,
    rd.lastupdated = $azure_update_tag
    WITH rd, rec_db
    MATCH (s:AzureSQLServer{id: rec_db.server_id})
    MERGE (s)-[r:RESOURCE]->(rd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_recoverable_databases,
        recoverable_databases_list=recoverable_databases,
        region='global',
        azure_update_tag=update_tag,
    )
    for recoverable_database in recoverable_databases:
        resource_group = get_azure_resource_group_name(recoverable_database.get('id'))
        _attach_resource_group_recoverable_database(neo4j_session, recoverable_database['id'], resource_group, update_tag)


def _attach_resource_group_recoverable_database(neo4j_session: neo4j.Session, recoverable_database_id: str, resource_group: str, update_tag: int) -> None:
    ingest_recoverable_databases = """
    MATCH (rd:AzureRecoverableDatabase{id: $rec_db_id})
    WITH rd
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (rd)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_recoverable_databases,
        rec_db_id=recoverable_database_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_restorable_dropped_databases(
        neo4j_session: neo4j.Session, restorable_dropped_databases: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the restorable dropped database details into neo4j.
    """
    ingest_restorable_dropped_databases = """
    UNWIND $restorable_dropped_databases_list as res_dropped_db
    MERGE (rdd:AzureRestorableDroppedDatabase{id: res_dropped_db.id})
    ON CREATE SET rdd.firstseen = timestamp(), rdd.location = res_dropped_db.location,
    rdd.region = res_dropped_db.location
    SET rdd.name = res_dropped_db.name,
    rdd.databasename = res_dropped_db.database_name,
    rdd.creationdate = res_dropped_db.creation_date,
    rdd.consolelink = res_dropped_db.consolelink,
    rdd.deletiondate = res_dropped_db.deletion_date,
    rdd.restoredate = res_dropped_db.earliest_restore_date,
    rdd.edition = res_dropped_db.edition,
    rdd.servicelevelobjective = res_dropped_db.service_level_objective,
    rdd.maxsizebytes = res_dropped_db.max_size_bytes,
    rdd.lastupdated = $azure_update_tag
    WITH rdd, res_dropped_db
    MATCH (s:AzureSQLServer{id: res_dropped_db.server_id})
    MERGE (s)-[r:RESOURCE]->(rdd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_restorable_dropped_databases,
        restorable_dropped_databases_list=restorable_dropped_databases,
        azure_update_tag=update_tag,
    )
    for restorable_dropped_database in restorable_dropped_databases:
        resource_group = get_azure_resource_group_name(restorable_dropped_database.get('id'))
        _attach_resource_group_restorable_dropped_database(neo4j_session, restorable_dropped_database['id'], resource_group, update_tag)


def _attach_resource_group_restorable_dropped_database(neo4j_session: neo4j.Session, restorable_dropped_database_id: str, resource_group: str, update_tag: int) -> None:
    ingest_restorable_dropped_databases = """
    MATCH (rdd:AzureRestorableDroppedDatabase{id: $res_dropped_db_id})
    WITH rdd
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (rdd)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_restorable_dropped_databases,
        res_dropped_db_id=restorable_dropped_database_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_failover_groups(
        neo4j_session: neo4j.Session, failover_groups: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the failover groups details into neo4j.
    """
    ingest_failover_groups = """
    UNWIND $failover_groups_list as fg
    MERGE (f:AzureFailoverGroup{id: fg.id})
    ON CREATE SET f.firstseen = timestamp(), f.location = fg.location
    SET f.name = fg.name,
    f.consolelink = fg.consolelink,
    f.replicationrole = fg.replication_role,
    f.replicationstate = fg.replication_state,
    f.lastupdated = $azure_update_tag
    WITH f, fg
    MATCH (s:AzureSQLServer{id: fg.server_id})
    MERGE (s)-[r:RESOURCE]->(f)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_failover_groups,
        failover_groups_list=failover_groups,
        azure_update_tag=update_tag,
    )
    for failover_group in failover_groups:
        resource_group = get_azure_resource_group_name(failover_group.get('id'))
        _attach_resource_group_restorable_failover_group(neo4j_session, failover_group['id'], resource_group, update_tag)


def _attach_resource_group_restorable_failover_group(neo4j_session: neo4j.Session, failover_group_id: str, resource_group: str, update_tag: int) -> None:
    ingest_failover_groups = """
    MATCH (f:AzureFailoverGroup{id: $fg_id})
    WITH f
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (f)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_failover_groups,
        fg_id=failover_group_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_elastic_pools(
        neo4j_session: neo4j.Session, elastic_pools: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the elastic pool details into neo4j.
    """
    ingest_elastic_pools = """
    UNWIND $elastic_pools_list as ep
    MERGE (e:AzureElasticPool{id: ep.id})
    ON CREATE SET e.firstseen = timestamp(), e.location = ep.location,
    e.region = ep.location
    SET e.name = ep.name,
    e.consolelink = ep.consolelink,
    e.kind = ep.kind,
    e.creationdate = ep.creation_date,
    e.state = ep.state,
    e.maxsizebytes = ep.max_size_bytes,
    e.licensetype = ep.license_type,
    e.zoneredundant = ep.zone_redundant,
    e.lastupdated = $azure_update_tag
    WITH e, ep
    MATCH (s:AzureSQLServer{id: ep.server_id})
    MERGE (s)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_elastic_pools,
        elastic_pools_list=elastic_pools,
        azure_update_tag=update_tag,
    )
    for elastic_pool in elastic_pools:
        resource_group = get_azure_resource_group_name(elastic_pool.get('id'))
        _attach_resource_group_restorable_elastic_pool(neo4j_session, elastic_pool['id'], resource_group, update_tag)


def _attach_resource_group_restorable_elastic_pool(neo4j_session: neo4j.Session, elastic_pool_id: str, resource_group: str, update_tag: int) -> None:
    ingest_elastic_pools = """
    MATCH (e:AzureElasticPool{id: $ep_id})
    WITH e
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (e)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_elastic_pools,
        ep_id=elastic_pool_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_databases(
        neo4j_session: neo4j.Session, databases: List[Dict], update_tag: int,
) -> None:
    """
    Ingest the database details into neo4j.
    """
    ingest_databases = """
    UNWIND $databases_list as az_database
    MERGE (d:AzureSQLDatabase{id: az_database.id})
    ON CREATE SET d.firstseen = timestamp(), d.location = az_database.location,
    d.region = az_database.location
    SET d.name = az_database.name,
    d.consolelink = az_database.consolelink,
    d.kind = az_database.kind,
    d.creationdate = az_database.creation_date,
    d.databaseid = az_database.database_id,
    d.maxsizebytes = az_database.max_size_bytes,
    d.licensetype = az_database.license_type,
    d.secondarylocation = az_database.default_secondary_location,
    d.elasticpoolid = az_database.elastic_pool_id,
    d.collation = az_database.collation,
    d.failovergroupid = az_database.failover_group_id,
    d.zoneredundant = az_database.zone_redundant,
    d.restorabledroppeddbid = az_database.restorable_dropped_database_id,
    d.recoverabledbid = az_database.recoverable_database_id,
    d.lastupdated = $azure_update_tag
    WITH d, az_database
    MATCH (s:AzureSQLServer{id: az_database.server_id})
    MERGE (s)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_databases,
        databases_list=databases,
        azure_update_tag=update_tag,
    )
    for database in databases:
        resource_group = get_azure_resource_group_name(database.get('id'))
        _attach_resource_group_restorable_database(neo4j_session, database['id'], resource_group, update_tag)


def _attach_resource_group_restorable_database(neo4j_session: neo4j.Session, database_id: str, resource_group: str, update_tag: int) -> None:
    ingest_databases = """
    MATCH (d:AzureSQLDatabase{id: $database_id})
    WITH d
    MATCH (s:AzureResourceGroup{name: $resource_group})
    MERGE (d)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_databases,
        database_id=database_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def sync_database_details(
        neo4j_session: neo4j.Session, credentials: Credentials,
        subscription_id: str, databases: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    db_details = get_database_details(credentials, subscription_id, databases)
    load_database_details(neo4j_session, db_details, update_tag, common_job_parameters)


@timeit
def get_database_details(
        credentials: Credentials, subscription_id: str, databases: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over the databases to get the details of resources in it.
    """
    for database in databases:
        replication_links = get_replication_links(credentials, subscription_id, database)
        db_threat_detection_policies = get_db_threat_detection_policies(credentials, subscription_id, database)
        restore_points = get_restore_points(credentials, subscription_id, database)
        transparent_data_encryptions = get_transparent_data_encryptions(credentials, subscription_id, database)
        yield database[
            'id'
        ], replication_links, db_threat_detection_policies, restore_points, transparent_data_encryptions


@timeit
def get_replication_links(credentials: Credentials, subscription_id: str, database: Dict) -> List[Dict]:
    """
    Returns the details of replication links in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        replication_links = list(
            map(
                lambda x: x.as_dict(),
                client.replication_links.list_by_database(
                    database['resource_group_name'],
                    database['server_name'],
                    database['name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving replication links - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Replication links resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving replication links - {e}")
        return []

    return replication_links


@timeit
def get_db_threat_detection_policies(credentials: Credentials, subscription_id: str, database: Dict) -> List[Dict]:
    """
    Returns the threat detection policy of a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        db_threat_detection_policies = client.database_threat_detection_policies.get(
            database['resource_group_name'],
            database['server_name'],
            database['name'],
            SecurityAlertPolicyName.DEFAULT,
        ).as_dict()
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving threat detection policy - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Threat detection policy resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving database threat detection policies - {e}")
        return []

    return db_threat_detection_policies


@timeit
def get_restore_points(credentials: Credentials, subscription_id: str, database: Dict) -> List[Dict]:
    """
    Returns the details of restore points in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        restore_points_list = list(
            map(
                lambda x: x.as_dict(),
                client.restore_points.list_by_database(
                    database['resource_group_name'],
                    database['server_name'],
                    database['name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving restore points - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Restore points resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving restore points - {e}")
        return []

    return restore_points_list


@timeit
def get_transparent_data_encryptions(credentials: Credentials, subscription_id: str, database: Dict) -> List[Dict]:
    """
    Returns the details of transparent data encryptions in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        transparent_data_encryptions_list = client.transparent_data_encryptions.get(
            database['resource_group_name'],
            database['server_name'],
            database['name'],
            TransparentDataEncryptionName.CURRENT,
        ).as_dict()
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving transparent data encryptions - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Transparent data encryptions resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving transparent data encryptions - {e}")
        return []

    return transparent_data_encryptions_list


@timeit
def get_firewall_rules(credentials: Credentials, subscription_id: str, server: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        firewall_rules = list(
            map(
                lambda x: x.as_dict(),
                client.firewall_rules.list_by_server(server['resourceGroup'], server['name']),
            ),
        )
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving Firewall Rules - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Firewall Rules resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving Azure Server Firewall Rules - {e}")
        return []
    return firewall_rules


@timeit
def load_database_details(
        neo4j_session: neo4j.Session, details: List[Tuple[Any, Any, Any, Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionaries for every resource in a database so we can import them in a single query
    """
    replication_links = []
    threat_detection_policies = []
    restore_points = []
    encryptions_list = []

    for databaseId, replication_link, db_threat_detection_policy, restore_point, transparent_data_encryption in details:
        if len(replication_link) > 0:
            for link in replication_link:
                link['consolelink'] = azure_console_link.get_console_link(
                    id=link['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                link['database_id'] = databaseId
                replication_links.append(link)

        if len(db_threat_detection_policy) > 0:
            db_threat_detection_policy['database_id'] = databaseId
            db_threat_detection_policy['consolelink'] = azure_console_link.get_console_link(
                id=db_threat_detection_policy['id'],
                primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            threat_detection_policies.append(db_threat_detection_policy)

        if len(restore_point) > 0:
            for point in restore_point:
                point['database_id'] = databaseId
                point['consolelink'] = azure_console_link.get_console_link(
                    id=point['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                restore_points.append(point)

        if len(transparent_data_encryption) > 0:
            transparent_data_encryption['database_id'] = databaseId
            transparent_data_encryption['consolelink'] = azure_console_link.get_console_link(
                id=transparent_data_encryption['id'],
                primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            encryptions_list.append(transparent_data_encryption)

    _load_replication_links(neo4j_session, replication_links, update_tag)
    _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag)
    _load_restore_points(neo4j_session, restore_points, update_tag)
    _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag)


@timeit
def _load_replication_links(
        neo4j_session: neo4j.Session, replication_links: List[Dict], update_tag: int,
) -> None:
    """
    Ingest replication links into neo4j.
    """
    ingest_replication_links = """
    UNWIND $replication_links_list as replication_link
    MERGE (rl:AzureReplicationLink{id: replication_link.id})
    ON CREATE SET rl.firstseen = timestamp(),
    rl.location = replication_link.location,
    rl.region = replication_link.location
    SET rl.name = replication_link.name,
    rl.partnerdatabase = replication_link.partner_database,
    rl.partnerlocation = replication_link.partner_location,
    rl.consolelink = replication_link.consolelink,
    rl.partnerrole = replication_link.partner_role,
    rl.partnerserver = replication_link.partner_server,
    rl.mode = replication_link.replication_mode,
    rl.state = replication_link.replication_state,
    rl.percentcomplete = replication_link.percent_complete,
    rl.role = replication_link.role,
    rl.starttime = replication_link.start_time,
    rl.terminationallowed = replication_link.is_termination_allowed,
    rl.lastupdated = $azure_update_tag
    WITH rl, replication_link
    MATCH (d:AzureSQLDatabase{id: replication_link.database_id})
    MERGE (d)-[r:CONTAINS]->(rl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_replication_links,
        replication_links_list=replication_links,
        azure_update_tag=update_tag,
    )
    for replication_link in replication_links:
        resource_group = get_azure_resource_group_name(replication_link.get('id'))
        _attach_resource_group_replication_link(neo4j_session, replication_link['id'], resource_group, update_tag)


def _attach_resource_group_replication_link(neo4j_session: neo4j.Session, replication_link_id: str, resource_group: str, update_tag: int) -> None:
    ingest_replication_links = """
    MATCH (rl:AzureReplicationLink{id: $replication_link_id})
    WITH rl
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (rl)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_replication_links,
        replication_link_id=replication_link_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_db_threat_detection_policies(
        neo4j_session: neo4j.Session, threat_detection_policies: List[Dict], update_tag: int,
) -> None:
    """
    Ingest threat detection policy into neo4j.
    """
    ingest_threat_detection_policies = """
    UNWIND $threat_detection_policies_list as tdp
    MERGE (policy:AzureDatabaseThreatDetectionPolicy{id: tdp.id})
    ON CREATE SET policy.firstseen = timestamp(),
    policy.location = tdp.location
    SET policy.name = tdp.name,
    policy.location = tdp.location,
    policy.region = tdp.location,
    policy.consolelink = tdp.consolelink,
    policy.kind = tdp.kind,
    policy.emailadmins = tdp.email_account_admins,
    policy.emailaddresses = tdp.email_addresses,
    policy.retentiondays = tdp.retention_days,
    policy.state = tdp.state,
    policy.storageendpoint = tdp.storage_endpoint,
    policy.useserverdefault = tdp.use_server_default,
    policy.disabledalerts = tdp.disabled_alerts,
    policy.lastupdated = $azure_update_tag
    WITH policy, tdp
    MATCH (d:AzureSQLDatabase{id: tdp.database_id})
    MERGE (d)-[r:CONTAINS]->(policy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_threat_detection_policies,
        threat_detection_policies_list=threat_detection_policies,
        azure_update_tag=update_tag,
    )
    for threat_detection in threat_detection_policies:
        resource_group = get_azure_resource_group_name(threat_detection.get('id'))
        _attach_resource_group_threat_detection(neo4j_session, threat_detection['id'], resource_group, update_tag)


def _attach_resource_group_threat_detection(neo4j_session: neo4j.Session, threat_detection_id: str, resource_group: str, update_tag: int) -> None:
    ingest_threat_detection_policies = """
    MATCH (policy:AzureDatabaseThreatDetectionPolicy{id: $threat_detection_id})
    WITH policy
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (policy)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_threat_detection_policies,
        threat_detection_id=threat_detection_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_restore_points(
        neo4j_session: neo4j.Session, restore_points: List[Dict], update_tag: int,
) -> None:
    """
    Ingest restore points into neo4j.
    """
    ingest_restore_points = """
    UNWIND $restore_points_list as rp
    MERGE (point:AzureRestorePoint{id: rp.id})
    ON CREATE SET point.firstseen = timestamp(),
    point.location = rp.location,
    point.region = rp.location
    SET point.name = rp.name,
    point.restoredate = rp.earliest_restore_date,
    point.restorepointtype = rp.restore_point_type,
    point.consolelink = rp.consolelink,
    point.creationdate = rp.restore_point_creation_date,
    point.lastupdated = $azure_update_tag
    WITH point, rp
    MATCH (d:AzureSQLDatabase{id: rp.database_id})
    MERGE (d)-[r:CONTAINS]->(point)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_restore_points,
        restore_points_list=restore_points,
        azure_update_tag=update_tag,
    )
    for restore_point in restore_points:
        resource_group = get_azure_resource_group_name(restore_point.get('id'))
        _attach_resource_group_restore_point(neo4j_session, restore_point['id'], resource_group, update_tag)


def _attach_resource_group_restore_point(neo4j_session: neo4j.Session, restore_point_id: str, resource_group: str, update_tag: int) -> None:
    ingest_restore_points = """
    MATCH (point:AzureRestorePoint{id: $restore_point_id})
    WITH point
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (point)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_restore_points,
        restore_point_id=restore_point_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_transparent_data_encryptions(
        neo4j_session: neo4j.Session, encryptions_list: List[Dict], update_tag: int,
) -> None:
    """
    Ingest transparent data encryptions into neo4j.
    """
    ingest_data_encryptions = """
    UNWIND $transparent_data_encryptions_list as e
    MERGE (tae:AzureTransparentDataEncryption{id: e.id})
    ON CREATE SET tae.firstseen = timestamp(),
    tae.location = e.location,
    tae.region = e.location
    SET tae.name = e.name,
    tae.status = e.status,
    tae.consolelink = tae.consolelink,
    tae.lastupdated = $azure_update_tag
    WITH tae, e
    MATCH (d:AzureSQLDatabase{id: e.database_id})
    MERGE (d)-[r:CONTAINS]->(tae)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_data_encryptions,
        transparent_data_encryptions_list=encryptions_list,
        azure_update_tag=update_tag,
    )
    for encryption in encryptions_list:
        resource_group = get_azure_resource_group_name(encryption.get('id'))
        _attach_resource_group_encryption(neo4j_session, encryption['id'], resource_group, update_tag)


def _attach_resource_group_encryption(neo4j_session: neo4j.Session, encryption_id: str, resource_group: str, update_tag: int) -> None:
    ingest_data_encryptions = """
    MATCH (tae:AzureTransparentDataEncryption{id: $encryption_id})
    WITH tae
    MATCH (d:AzureResourceGroup{name: $resource_group})
    MERGE (tae)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_data_encryptions,
        encryption_id=encryption_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def cleanup_azure_sql_servers(
        neo4j_session: neo4j.Session, common_job_parameters: Dict,
) -> None:
    run_cleanup_job('azure_sql_server_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        sync_tag: int, common_job_parameters: Dict, regions: list,
) -> None:
    logger.info("Syncing Azure SQL for subscription '%s'.", subscription_id)
    server_list = get_server_list(credentials, subscription_id, regions, common_job_parameters)
    load_server_data(neo4j_session, subscription_id, server_list, sync_tag)
    load_server_private_endpoint_connection(neo4j_session, server_list, sync_tag)
    sync_server_details(neo4j_session, credentials, subscription_id, server_list, sync_tag, common_job_parameters)
    cleanup_azure_sql_servers(neo4j_session, common_job_parameters)
