import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Tuple

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sql.models import SecurityAlertPolicyName
from azure.mgmt.sql.models import TransparentDataEncryptionName
from msrestazure.azure_exceptions import CloudError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.models.azure.sql.databasethreatdetectionpolicy import (
    AzureDatabaseThreatDetectionPolicySchema,
)
from cartography.models.azure.sql.elasticpool import AzureElasticPoolSchema
from cartography.models.azure.sql.failovergroup import AzureFailoverGroupSchema
from cartography.models.azure.sql.recoverabledatabase import (
    AzureRecoverableDatabaseSchema,
)
from cartography.models.azure.sql.replicationlink import AzureReplicationLinkSchema
from cartography.models.azure.sql.restorabledroppeddatabase import (
    AzureRestorableDroppedDatabaseSchema,
)
from cartography.models.azure.sql.restorepoint import AzureRestorePointSchema
from cartography.models.azure.sql.serveradadministrator import (
    AzureServerADAdministratorSchema,
)
from cartography.models.azure.sql.serverdnsalias import AzureServerDNSAliasSchema
from cartography.models.azure.sql.sqldatabase import AzureSQLDatabaseSchema
from cartography.models.azure.sql.sqlserver import AzureSQLServerSchema
from cartography.models.azure.sql.sqlserver_firewall_rule import (
    AzureSQLServerFirewallRuleSchema,
)
from cartography.models.azure.sql.transparentdataencryption import (
    AzureTransparentDataEncryptionSchema,
)
from cartography.models.azure.tags.sql_tag import AzureSQLServerTagsSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _copy_properties(data: Dict, mapping: Mapping[str, tuple[str, ...]]) -> Dict:
    properties = data.get("properties") or {}
    for target, sources in mapping.items():
        if target in data:
            continue
        for source in sources:
            if source in properties:
                data[target] = properties[source]
                break
    return data


SQL_SERVER_PROPERTY_MAP = {
    "state": ("state",),
    "version": ("version",),
    "public_network_access": ("public_network_access", "publicNetworkAccess"),
    "minimal_tls_version": ("minimal_tls_version", "minimalTlsVersion"),
}

SQL_DATABASE_PROPERTY_MAP = {
    "creation_date": ("creation_date", "creationDate"),
    "database_id": ("database_id", "databaseId"),
    "max_size_bytes": ("max_size_bytes", "maxSizeBytes"),
    "license_type": ("license_type", "licenseType"),
    "default_secondary_location": (
        "default_secondary_location",
        "defaultSecondaryLocation",
    ),
    "elastic_pool_id": ("elastic_pool_id", "elasticPoolId"),
    "collation": ("collation",),
    "failover_group_id": ("failover_group_id", "failoverGroupId"),
    "zone_redundant": ("zone_redundant", "zoneRedundant"),
    "restorable_dropped_database_id": (
        "restorable_dropped_database_id",
        "restorableDroppedDatabaseId",
    ),
    "recoverable_database_id": ("recoverable_database_id", "recoverableDatabaseId"),
}

SQL_FIREWALL_RULE_PROPERTY_MAP = {
    "start_ip_address": ("start_ip_address", "startIpAddress"),
    "end_ip_address": ("end_ip_address", "endIpAddress"),
}

SQL_DETAIL_PROPERTY_MAP = {
    "administrator_type": ("administrator_type", "administratorType"),
    "azure_dns_record": ("azure_dns_record", "azureDnsRecord"),
    "creation_date": ("creation_date", "creationDate"),
    "creation_time": ("creation_time", "creationTime"),
    "database_name": ("database_name", "databaseName"),
    "default_secondary_location": (
        "default_secondary_location",
        "defaultSecondaryLocation",
    ),
    "deletion_date": ("deletion_date", "deletionDate"),
    "disabled_alerts": ("disabled_alerts", "disabledAlerts"),
    "earliest_restore_date": ("earliest_restore_date", "earliestRestoreDate"),
    "email_account_admins": ("email_account_admins", "emailAccountAdmins"),
    "email_addresses": ("email_addresses", "emailAddresses"),
    "is_termination_allowed": ("is_termination_allowed", "isTerminationAllowed"),
    "last_available_backup_date": (
        "last_available_backup_date",
        "lastAvailableBackupDate",
    ),
    "license_type": ("license_type", "licenseType"),
    "max_size_bytes": ("max_size_bytes", "maxSizeBytes"),
    "partner_database": ("partner_database", "partnerDatabase"),
    "partner_location": ("partner_location", "partnerLocation"),
    "partner_role": ("partner_role", "partnerRole"),
    "partner_server": ("partner_server", "partnerServer"),
    "percent_complete": ("percent_complete", "percentComplete"),
    "replication_mode": ("replication_mode", "replicationMode"),
    "replication_role": ("replication_role", "replicationRole"),
    "replication_state": ("replication_state", "replicationState"),
    "restore_point_creation_date": (
        "restore_point_creation_date",
        "restorePointCreationDate",
    ),
    "restore_point_type": ("restore_point_type", "restorePointType"),
    "retention_days": ("retention_days", "retentionDays"),
    "service_level_objective": ("service_level_objective", "serviceLevelObjective"),
    "start_time": ("start_time", "startTime"),
    "state": ("state",),
    "status": ("status",),
    "storage_endpoint": ("storage_endpoint", "storageEndpoint"),
    "zone_redundant": ("zone_redundant", "zoneRedundant"),
}


def transform_sql_server(server: Dict) -> Dict:
    return _copy_properties(server, SQL_SERVER_PROPERTY_MAP)


def transform_sql_database(database: Dict) -> Dict:
    return _copy_properties(database, SQL_DATABASE_PROPERTY_MAP)


def transform_sql_firewall_rule(rule: Dict) -> Dict:
    return _copy_properties(rule, SQL_FIREWALL_RULE_PROPERTY_MAP)


def transform_sql_detail(data: Dict) -> Dict:
    return _copy_properties(data, SQL_DETAIL_PROPERTY_MAP)


@timeit
def get_client(credentials: Credentials, subscription_id: str) -> SqlManagementClient:
    """
    Getting the Azure SQL client
    """
    client = SqlManagementClient(credentials, subscription_id)
    return client


@timeit
def get_server_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Returning the list of Azure SQL servers.
    """
    try:
        client = get_client(credentials, subscription_id)
        server_list = list(
            map(lambda x: transform_sql_server(x.as_dict()), client.servers.list())
        )

    # ClientAuthenticationError and ResourceNotFoundError are subclasses under HttpResponseError
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving servers - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Server resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving servers - {e}")
        return []

    for server in server_list:
        x = server["id"].split("/")
        server["resourceGroup"] = x[x.index("resourceGroups") + 1]
    return server_list


@timeit
def load_server_data(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    server_list: List[Dict],
    azure_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureSQLServerSchema(),
        server_list,
        lastupdated=azure_update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_server_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    server_list: List[Dict],
    sync_tag: int,
) -> None:
    details = get_server_details(credentials, subscription_id, server_list)
    load_server_details(neo4j_session, credentials, subscription_id, details, sync_tag)


@timeit
def get_server_details(
    credentials: Credentials,
    subscription_id: str,
    server_list: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over each servers to get its resource details.
    """
    for server in server_list:
        dns_alias = get_dns_aliases(credentials, subscription_id, server)
        ad_admins = get_ad_admins(credentials, subscription_id, server)
        r_databases = get_recoverable_databases(credentials, subscription_id, server)
        rd_databases = get_restorable_dropped_databases(
            credentials,
            subscription_id,
            server,
        )
        fgs = get_failover_groups(credentials, subscription_id, server)
        elastic_pools = get_elastic_pools(credentials, subscription_id, server)
        databases = get_databases(credentials, subscription_id, server)
        firewall_rules = get_firewall_rules(credentials, subscription_id, server)
        yield server["id"], server["name"], server[
            "resourceGroup"
        ], dns_alias, ad_admins, r_databases, rd_databases, fgs, elastic_pools, databases, firewall_rules


@timeit
def get_dns_aliases(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of the DNS aliases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        dns_aliases = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.server_dns_aliases.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving DNS Aliases - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"DNS Alias resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving Azure Server DNS Aliases - {e}")
        return []

    return dns_aliases


@timeit
def get_ad_admins(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of the Server AD Administrators in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        ad_admins = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.server_azure_ad_administrators.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving Azure AD Administrators - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Azure AD Administrators resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving server azure AD Administrators - {e}")
        return []

    return ad_admins


@timeit
def get_recoverable_databases(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of the Recoverable databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        recoverable_databases = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.recoverable_databases.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except CloudError:
        # The API returns a '404 CloudError: Not Found for url: <url>' if no recoverable databases are present.
        return []
    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving recoverable databases - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Recoverable databases resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving recoverable databases - {e}")
        return []

    return recoverable_databases


@timeit
def get_restorable_dropped_databases(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of the Restorable Dropped Databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        restorable_dropped_databases = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.restorable_dropped_databases.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving Restorable Dropped Databases - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Restorable Dropped Databases resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving restorable dropped databases - {e}")
        return []

    return restorable_dropped_databases


@timeit
def get_failover_groups(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of Failover groups in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        failover_groups = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.failover_groups.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving Failover groups - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Failover groups resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving failover groups - {e}")
        return []

    return failover_groups


@timeit
def get_elastic_pools(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of Elastic Pools in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        elastic_pools = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.elastic_pools.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving Elastic Pools - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Elastic Pools resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving elastic pools - {e}")
        return []

    return elastic_pools


@timeit
def get_firewall_rules(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of the firewall rules in a SQL server.
    """
    try:
        client = get_client(credentials, subscription_id)
        firewall_rules = list(
            map(
                lambda x: transform_sql_firewall_rule(x.as_dict()),
                client.firewall_rules.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving firewall rules - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Firewall rules resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving firewall rules - {e}")
        return []

    return firewall_rules


@timeit
def get_databases(
    credentials: Credentials,
    subscription_id: str,
    server: Dict,
) -> List[Dict]:
    """
    Returns details of Databases in a SQL server.
    """
    try:
        client = get_client(credentials, subscription_id)
        databases = list(
            map(
                lambda x: transform_sql_database(x.as_dict()),
                client.databases.list_by_server(
                    server["resourceGroup"],
                    server["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving SQL databases - {e}",
        )
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
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    details: Iterable[Tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]],
    update_tag: int,
) -> None:
    dns_aliases = []
    ad_admins = []
    recoverable_databases = []
    restorable_dropped_databases = []
    failover_groups = []
    elastic_pools = []
    databases = []
    firewall_rules: List[Dict] = []

    for (
        server_id,
        name,
        rg,
        dns_alias,
        ad_admin,
        r_database,
        rd_database,
        fg,
        elastic_pool,
        database,
        firewall_rule,
    ) in details:
        if len(dns_alias) > 0:
            for alias in dns_alias:
                alias["server_name"] = name
                alias["server_id"] = server_id
                dns_aliases.append(alias)

        if len(ad_admin) > 0:
            for admin in ad_admin:
                admin["server_name"] = name
                admin["server_id"] = server_id
                ad_admins.append(admin)

        if len(r_database) > 0:
            for rdb in r_database:
                rdb["server_name"] = name
                rdb["server_id"] = server_id
                recoverable_databases.append(rdb)

        if len(rd_database) > 0:
            for rddb in rd_database:
                rddb["server_name"] = name
                rddb["server_id"] = server_id
                restorable_dropped_databases.append(rddb)

        if len(fg) > 0:
            for group in fg:
                group["server_name"] = name
                group["server_id"] = server_id
                failover_groups.append(group)

        if len(elastic_pool) > 0:
            for pool in elastic_pool:
                pool["server_name"] = name
                pool["server_id"] = server_id
                elastic_pools.append(pool)

        if len(database) > 0:
            for db in database:
                db["server_name"] = name
                db["server_id"] = server_id
                db["resource_group_name"] = rg
                databases.append(db)

        if len(firewall_rule) > 0:
            for fr in firewall_rule:
                fr_props = fr.get("properties", {})
                fr["start_ip_address"] = fr.get("start_ip_address") or fr_props.get(
                    "start_ip_address"
                )
                fr["end_ip_address"] = fr.get("end_ip_address") or fr_props.get(
                    "end_ip_address"
                )
                fr["server_id"] = server_id
                firewall_rules.append(fr)

    _load_elastic_pools(neo4j_session, elastic_pools, subscription_id, update_tag)
    _load_failover_groups(neo4j_session, failover_groups, subscription_id, update_tag)
    _load_databases(neo4j_session, databases, subscription_id, update_tag)
    _load_recoverable_databases(
        neo4j_session, recoverable_databases, subscription_id, update_tag
    )
    _load_restorable_dropped_databases(
        neo4j_session,
        restorable_dropped_databases,
        subscription_id,
        update_tag,
    )
    _load_server_dns_aliases(neo4j_session, dns_aliases, subscription_id, update_tag)
    _load_server_ad_admins(neo4j_session, ad_admins, subscription_id, update_tag)
    _load_firewall_rules(neo4j_session, firewall_rules, subscription_id, update_tag)

    sync_database_details(
        neo4j_session,
        credentials,
        subscription_id,
        databases,
        update_tag,
    )


@timeit
def _load_server_dns_aliases(
    neo4j_session: neo4j.Session,
    dns_aliases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the DNS Alias details into neo4j.
    """
    load(
        neo4j_session,
        AzureServerDNSAliasSchema(),
        dns_aliases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_server_ad_admins(
    neo4j_session: neo4j.Session,
    ad_admins: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the Server AD Administrators details into neo4j.
    """
    load(
        neo4j_session,
        AzureServerADAdministratorSchema(),
        ad_admins,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_recoverable_databases(
    neo4j_session: neo4j.Session,
    recoverable_databases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the recoverable database details into neo4j.
    """
    load(
        neo4j_session,
        AzureRecoverableDatabaseSchema(),
        recoverable_databases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_restorable_dropped_databases(
    neo4j_session: neo4j.Session,
    restorable_dropped_databases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the restorable dropped database details into neo4j.
    """
    load(
        neo4j_session,
        AzureRestorableDroppedDatabaseSchema(),
        restorable_dropped_databases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_failover_groups(
    neo4j_session: neo4j.Session,
    failover_groups: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the failover groups details into neo4j.
    """
    load(
        neo4j_session,
        AzureFailoverGroupSchema(),
        failover_groups,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_elastic_pools(
    neo4j_session: neo4j.Session,
    elastic_pools: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the elastic pool details into neo4j.
    """
    load(
        neo4j_session,
        AzureElasticPoolSchema(),
        elastic_pools,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_databases(
    neo4j_session: neo4j.Session,
    databases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest the database details into neo4j.
    """
    load(
        neo4j_session,
        AzureSQLDatabaseSchema(),
        databases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_firewall_rules(
    neo4j_session: neo4j.Session,
    firewall_rules: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest SQL Server firewall rule details into neo4j.
    """
    load(
        neo4j_session,
        AzureSQLServerFirewallRuleSchema(),
        firewall_rules,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_sql_server_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    servers: List[Dict],
    update_tag: int,
) -> None:
    """
    Loads tags for SQL Servers.
    """
    tags = transform_tags(servers, subscription_id)
    load(
        neo4j_session,
        AzureSQLServerTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_database_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    databases: List[Dict],
    update_tag: int,
) -> None:
    db_details = get_database_details(credentials, subscription_id, databases)
    load_database_details(neo4j_session, db_details, subscription_id, update_tag)  # type: ignore


@timeit
def get_database_details(
    credentials: Credentials,
    subscription_id: str,
    databases: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over the databases to get the details of resources in it.
    """
    for database in databases:
        replication_links = get_replication_links(
            credentials,
            subscription_id,
            database,
        )
        db_threat_detection_policies = get_db_threat_detection_policies(
            credentials,
            subscription_id,
            database,
        )
        restore_points = get_restore_points(credentials, subscription_id, database)
        transparent_data_encryptions = get_transparent_data_encryptions(
            credentials,
            subscription_id,
            database,
        )
        yield database[
            "id"
        ], replication_links, db_threat_detection_policies, restore_points, transparent_data_encryptions


@timeit
def get_replication_links(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the details of replication links in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        replication_links = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.replication_links.list_by_database(
                    database["resource_group_name"],
                    database["server_name"],
                    database["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving replication links - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Replication links resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving replication links - {e}")
        return []

    return replication_links


@timeit
def get_db_threat_detection_policies(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the threat detection policy of a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        db_threat_detection_policies = client.database_security_alert_policies.get(
            database["resource_group_name"],
            database["server_name"],
            database["name"],
            SecurityAlertPolicyName.DEFAULT,
        ).as_dict()
        db_threat_detection_policies = transform_sql_detail(
            db_threat_detection_policies
        )
    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving threat detection policy - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Threat detection policy resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(
            f"Error while retrieving database threat detection policies - {e}",
        )
        return []

    return db_threat_detection_policies


@timeit
def get_restore_points(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the details of restore points in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        restore_points_list = list(
            map(
                lambda x: transform_sql_detail(x.as_dict()),
                client.restore_points.list_by_database(
                    database["resource_group_name"],
                    database["server_name"],
                    database["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving restore points - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Restore points resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving restore points - {e}")
        return []

    return restore_points_list


@timeit
def get_transparent_data_encryptions(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the details of transparent data encryptions in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        transparent_data_encryptions_list = client.transparent_data_encryptions.get(
            database["resource_group_name"],
            database["server_name"],
            database["name"],
            TransparentDataEncryptionName.CURRENT,
        ).as_dict()
        transparent_data_encryptions_list = transform_sql_detail(
            transparent_data_encryptions_list
        )
    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving transparent data encryptions - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Transparent data encryptions resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving transparent data encryptions - {e}")
        return []

    return transparent_data_encryptions_list


@timeit
def load_database_details(
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any, Any, Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionaries for every resource in a database so we can import them in a single query
    """
    replication_links = []
    threat_detection_policies = []
    restore_points = []
    encryptions_list = []

    for (
        databaseId,
        replication_link,
        db_threat_detection_policy,
        restore_point,
        transparent_data_encryption,
    ) in details:
        if len(replication_link) > 0:
            for link in replication_link:
                link["database_id"] = databaseId
                replication_links.append(link)

        if len(db_threat_detection_policy) > 0:
            db_threat_detection_policy["database_id"] = databaseId
            threat_detection_policies.append(db_threat_detection_policy)

        if len(restore_point) > 0:
            for point in restore_point:
                point["database_id"] = databaseId
                restore_points.append(point)

        if len(transparent_data_encryption) > 0:
            transparent_data_encryption["database_id"] = databaseId
            encryptions_list.append(transparent_data_encryption)

    _load_replication_links(
        neo4j_session, replication_links, subscription_id, update_tag
    )
    _load_db_threat_detection_policies(
        neo4j_session,
        threat_detection_policies,
        subscription_id,
        update_tag,
    )
    _load_restore_points(neo4j_session, restore_points, subscription_id, update_tag)
    _load_transparent_data_encryptions(
        neo4j_session, encryptions_list, subscription_id, update_tag
    )


@timeit
def _load_replication_links(
    neo4j_session: neo4j.Session,
    replication_links: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest replication links into neo4j.
    """
    load(
        neo4j_session,
        AzureReplicationLinkSchema(),
        replication_links,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_db_threat_detection_policies(
    neo4j_session: neo4j.Session,
    threat_detection_policies: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest threat detection policy into neo4j.
    """
    load(
        neo4j_session,
        AzureDatabaseThreatDetectionPolicySchema(),
        threat_detection_policies,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_restore_points(
    neo4j_session: neo4j.Session,
    restore_points: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest restore points into neo4j.
    """
    load(
        neo4j_session,
        AzureRestorePointSchema(),
        restore_points,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_transparent_data_encryptions(
    neo4j_session: neo4j.Session,
    encryptions_list: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest transparent data encryptions into neo4j.
    """
    load(
        neo4j_session,
        AzureTransparentDataEncryptionSchema(),
        encryptions_list,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_azure_sql_servers(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    for node in [
        AzureSQLServerSchema,
        AzureServerDNSAliasSchema,
        AzureServerADAdministratorSchema,
        AzureReplicationLinkSchema,
        AzureRestorePointSchema,
        AzureTransparentDataEncryptionSchema,
        AzureDatabaseThreatDetectionPolicySchema,
        AzureSQLDatabaseSchema,
        AzureSQLServerFirewallRuleSchema,
        AzureElasticPoolSchema,
        AzureFailoverGroupSchema,
        AzureRecoverableDatabaseSchema,
        AzureRestorableDroppedDatabaseSchema,
    ]:
        GraphJob.from_node_schema(node(), common_job_parameters).run(
            neo4j_session,
        )


@timeit
def cleanup_sql_server_tags(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Runs cleanup job for Azure SQL Server tags.
    """
    GraphJob.from_node_schema(AzureSQLServerTagsSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    sync_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure SQL for subscription '%s'.", subscription_id)
    server_list = get_server_list(credentials, subscription_id)
    load_server_data(neo4j_session, subscription_id, server_list, sync_tag)
    load_sql_server_tags(neo4j_session, subscription_id, server_list, sync_tag)
    sync_server_details(
        neo4j_session,
        credentials,
        subscription_id,
        server_list,
        sync_tag,
    )
    cleanup_azure_sql_servers(neo4j_session, common_job_parameters)
    cleanup_sql_server_tags(neo4j_session, common_job_parameters)
