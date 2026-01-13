import logging
import uuid
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.cosmosdb import CosmosDBManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.cosmosdb.account import AzureCosmosDBAccountSchema
from cartography.models.azure.cosmosdb.accountfailoverpolicy import (
    AzureCosmosDBAccountFailoverPolicySchema,
)
from cartography.models.azure.cosmosdb.cassandrakeyspace import (
    AzureCosmosDBCassandraKeyspaceSchema,
)
from cartography.models.azure.cosmosdb.cassandratable import (
    AzureCosmosDBCassandraTableSchema,
)
from cartography.models.azure.cosmosdb.corspolicy import AzureCosmosDBCorsPolicySchema
from cartography.models.azure.cosmosdb.dblocation import AzureCosmosDBLocationSchema
from cartography.models.azure.cosmosdb.mongodbcollection import (
    AzureCosmosDBMongoDBCollectionSchema,
)
from cartography.models.azure.cosmosdb.mongodbdatabase import (
    AzureCosmosDBMongoDBDatabaseSchema,
)
from cartography.models.azure.cosmosdb.privateendpointconnection import (
    AzureCDBPrivateEndpointConnectionSchema,
)
from cartography.models.azure.cosmosdb.sqlcontainer import (
    AzureCosmosDBSqlContainerSchema,
)
from cartography.models.azure.cosmosdb.sqldatabase import AzureCosmosDBSqlDatabaseSchema
from cartography.models.azure.cosmosdb.tableresource import (
    AzureCosmosDBTableResourceSchema,
)
from cartography.models.azure.cosmosdb.virtualnetworkrule import (
    AzureCosmosDBVirtualNetworkRuleSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_client(
    credentials: Credentials,
    subscription_id: str,
) -> CosmosDBManagementClient:
    """
    Getting the CosmosDB client
    """
    client = CosmosDBManagementClient(credentials, subscription_id)
    return client


@timeit
def get_database_account_list(
    credentials: Credentials,
    subscription_id: str,
) -> List[Dict]:
    """
    Get a list of all database accounts.
    """
    try:
        client = get_client(credentials, subscription_id)
        database_account_list = list(
            map(lambda x: x.as_dict(), client.database_accounts.list()),
        )

    # ClientAuthenticationError and ResourceNotFoundError are subclasses under HttpResponseError
    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving database accounts",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("Database Account not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving database accounts", exc_info=True)
        return []

    for database_account in database_account_list:
        x = database_account["id"].split("/")
        database_account["resourceGroup"] = x[x.index("resourceGroups") + 1]

    return database_account_list


@timeit
def transform_database_account_data(database_account_list: List[Dict]) -> List[Dict]:
    """
    Transforming the database account response for neo4j ingestion.
    """
    for database_account in database_account_list:
        capabilities: List[str] = []
        iprules: List[str] = []
        if (
            "capabilities" in database_account
            and len(database_account["capabilities"]) > 0
        ):
            capabilities = [x["name"] for x in database_account["capabilities"]]
        if "ip_rules" in database_account and len(database_account["ip_rules"]) > 0:
            iprules = [x["ip_address_or_range"] for x in database_account["ip_rules"]]
        database_account["ipruleslist"] = iprules
        database_account["capabilities"] = capabilities

    return database_account_list


@timeit
def load_database_account_data(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    database_account_list: List[Dict],
    azure_update_tag: int,
) -> None:
    """
    Ingest data of all database accounts into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBAccountSchema(),
        database_account_list,
        lastupdated=azure_update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_database_account_data_resources(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    database_account_list: List[Dict],
    azure_update_tag: int,
) -> None:
    """
    This function calls the load functions for the resources that are present as a part of the database account
    response (like cors policy, failover policy, private endpoint connections, virtual network rules and locations).
    """
    for database_account in database_account_list:
        _load_cosmosdb_cors_policy(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_cosmosdb_failover_policies(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_cosmosdb_private_endpoint_connections(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_cosmosdb_virtual_network_rules(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_database_account_write_locations(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_database_account_read_locations(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )
        _load_database_account_associated_locations(
            neo4j_session,
            database_account,
            subscription_id,
            azure_update_tag,
        )


@timeit
def _load_database_account_write_locations(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of location with write permission enabled.
    """
    if (
        "write_locations" in database_account
        and len(database_account["write_locations"]) > 0
    ):
        write_locations = database_account["write_locations"]
        for wl in write_locations:
            wl["db_write_account_id"] = database_account["id"]

        load(
            neo4j_session,
            AzureCosmosDBLocationSchema(),
            write_locations,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
        )


@timeit
def _load_database_account_read_locations(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of location with read permission enabled.
    """
    if (
        "read_locations" in database_account
        and len(database_account["read_locations"]) > 0
    ):
        read_locations = database_account["read_locations"]
        for rl in read_locations:
            rl["db_read_account_id"] = database_account["id"]

        load(
            neo4j_session,
            AzureCosmosDBLocationSchema(),
            read_locations,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
        )


@timeit
def _load_database_account_associated_locations(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of enabled location for the database account.
    """
    if "locations" in database_account and len(database_account["locations"]) > 0:
        associated_locations = database_account["locations"]
        for al in associated_locations:
            al["db_associated_account_id"] = database_account["id"]

        load(
            neo4j_session,
            AzureCosmosDBLocationSchema(),
            associated_locations,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
        )


@timeit
def transform_cosmosdb_cors_policy(database_account: Dict) -> Dict:
    """
    Transform CosmosDB Cors Policy response for neo4j ingestion.
    """
    for policy in database_account["cors"]:
        if "cors_policy_unique_id" not in policy:
            policy["cors_policy_unique_id"] = str(uuid.uuid4())

    return database_account


@timeit
def _load_cosmosdb_cors_policy(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of the Cors Policy of the database account.
    """
    if "cors" in database_account and len(database_account["cors"]) > 0:
        database_account = transform_cosmosdb_cors_policy(database_account)
        database_account_id = database_account["id"]
        cors_policies = database_account["cors"]

        load(
            neo4j_session,
            AzureCosmosDBCorsPolicySchema(),
            cors_policies,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
            DatabaseAccountId=database_account_id,
        )


@timeit
def _load_cosmosdb_failover_policies(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of the Failover Policies of the database account.
    """
    if (
        "failover_policies" in database_account
        and len(database_account["failover_policies"]) > 0
    ):
        database_account_id = database_account["id"]
        failover_policies = database_account["failover_policies"]

        load(
            neo4j_session,
            AzureCosmosDBAccountFailoverPolicySchema(),
            failover_policies,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
            DatabaseAccountId=database_account_id,
        )


@timeit
def _load_cosmosdb_private_endpoint_connections(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of the Private Endpoint Connections of the database account.
    """
    if (
        "private_endpoint_connections" in database_account
        and len(
            database_account["private_endpoint_connections"],
        )
        > 0
    ):
        database_account_id = database_account["id"]
        private_endpoint_connections = database_account["private_endpoint_connections"]

        load(
            neo4j_session,
            AzureCDBPrivateEndpointConnectionSchema(),
            private_endpoint_connections,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
            DatabaseAccountId=database_account_id,
        )


@timeit
def _load_cosmosdb_virtual_network_rules(
    neo4j_session: neo4j.Session,
    database_account: Dict,
    subscription_id: str,
    azure_update_tag: int,
) -> None:
    """
    Ingest the details of the Virtual Network Rules of the database account.
    """
    if (
        "virtual_network_rules" in database_account
        and len(database_account["virtual_network_rules"]) > 0
    ):
        database_account_id = database_account["id"]
        virtual_network_rules = database_account["virtual_network_rules"]

        load(
            neo4j_session,
            AzureCosmosDBVirtualNetworkRuleSchema(),
            virtual_network_rules,
            lastupdated=azure_update_tag,
            AZURE_SUBSCRIPTION_ID=subscription_id,
            DatabaseAccountId=database_account_id,
        )


@timeit
def sync_database_account_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    database_account_list: List[Dict],
    sync_tag: int,
    common_job_parameters: Dict,
) -> None:
    details = get_database_account_details(
        credentials,
        subscription_id,
        database_account_list,
    )
    load_database_account_details(
        neo4j_session,
        credentials,
        subscription_id,
        details,
        sync_tag,
        common_job_parameters,
    )


@timeit
def get_database_account_details(
    credentials: Credentials,
    subscription_id: str,
    database_account_list: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over the database accounts and return the list of SQL and MongoDB databases, Cassandra keyspaces and
    table resources associated with each database account.
    """
    for database_account in database_account_list:
        sql_databases = get_sql_databases(
            credentials,
            subscription_id,
            database_account,
        )
        cassandra_keyspaces = get_cassandra_keyspaces(
            credentials,
            subscription_id,
            database_account,
        )
        mongodb_databases = get_mongodb_databases(
            credentials,
            subscription_id,
            database_account,
        )
        table_resources = get_table_resources(
            credentials,
            subscription_id,
            database_account,
        )
        yield database_account["id"], database_account["name"], database_account[
            "resourceGroup"
        ], sql_databases, cassandra_keyspaces, mongodb_databases, table_resources


@timeit
def get_sql_databases(
    credentials: Credentials,
    subscription_id: str,
    database_account: Dict,
) -> List[Dict]:
    """
    Return the list of SQL Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        sql_database_list = list(
            map(
                lambda x: x.as_dict(),
                client.sql_resources.list_sql_databases(
                    database_account["resourceGroup"],
                    database_account["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving SQL databases",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("SQL databases resource not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving SQL Database list", exc_info=True)
        return []

    return sql_database_list


@timeit
def get_cassandra_keyspaces(
    credentials: Credentials,
    subscription_id: str,
    database_account: Dict,
) -> List[Dict]:
    """
    Return the list of Cassandra Keyspaces in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        cassandra_keyspace_list = list(
            map(
                lambda x: x.as_dict(),
                client.cassandra_resources.list_cassandra_keyspaces(
                    database_account["resourceGroup"],
                    database_account["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving Cassandra keyspaces",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("Cassandra keyspaces resource not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving Cassandra keyspaces list", exc_info=True)
        return []

    return cassandra_keyspace_list


@timeit
def get_mongodb_databases(
    credentials: Credentials,
    subscription_id: str,
    database_account: Dict,
) -> List[Dict]:
    """
    Return the list of MongoDB Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        mongodb_database_list = list(
            map(
                lambda x: x.as_dict(),
                client.mongo_db_resources.list_mongo_db_databases(
                    database_account["resourceGroup"],
                    database_account["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving MongoDB Databases",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("MongoDB Databases resource not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving MongoDB Databases list", exc_info=True)
        return []

    return mongodb_database_list


@timeit
def get_table_resources(
    credentials: Credentials,
    subscription_id: str,
    database_account: Dict,
) -> List[Dict]:
    """
    Return the list of Table Resources in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        table_resources_list = list(
            map(
                lambda x: x.as_dict(),
                client.table_resources.list_tables(
                    database_account["resourceGroup"],
                    database_account["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving Table resources",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("Table resource not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving Table resources list", exc_info=True)
        return []

    return table_resources_list


@timeit
def transform_database_account_resources(
    account_id: Any,
    name: Any,
    resource_group: Any,
    resources: List[Dict],
) -> List[Dict]:
    """
    Transform the SQL Database/Cassandra Keyspace/MongoDB Database/Table Resource response for neo4j ingestion.
    """
    for resource in resources:
        resource["database_account_name"] = name
        resource["database_account_id"] = account_id
        resource["resource_group_name"] = resource_group
    return resources


@timeit
def load_database_account_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    details: List[Tuple[Any, Any, Any, Any, Any, Any, Any]],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Create dictionaries for SQL Databases, Cassandra Keyspaces, MongoDB Databases and table resources.
    """
    sql_databases: List[Dict] = []
    cassandra_keyspaces: List[Dict] = []
    mongodb_databases: List[Dict] = []
    table_resources: List[Dict] = []

    for (
        account_id,
        name,
        resourceGroup,
        sql_database,
        cassandra_keyspace,
        mongodb_database,
        table,
    ) in details:
        if len(sql_database) > 0:
            dbs = transform_database_account_resources(
                account_id,
                name,
                resourceGroup,
                sql_database,
            )
            sql_databases.extend(dbs)

        if len(cassandra_keyspace) > 0:
            keyspaces = transform_database_account_resources(
                account_id,
                name,
                resourceGroup,
                cassandra_keyspace,
            )
            cassandra_keyspaces.extend(keyspaces)

        if len(mongodb_database) > 0:
            mongo_dbs = transform_database_account_resources(
                account_id,
                name,
                resourceGroup,
                mongodb_database,
            )
            mongodb_databases.extend(mongo_dbs)

        if len(table) > 0:
            t = transform_database_account_resources(
                account_id,
                name,
                resourceGroup,
                table,
            )
            table_resources.extend(t)

    # Loading the table resources
    _load_table_resources(neo4j_session, table_resources, subscription_id, update_tag)
    # Cleanup of table resources (done here because table resource doesn't have any other child resources in it)
    cleanup_table_resources(neo4j_session, common_job_parameters)

    # Loading SQL databases, Cassandra Keyspaces and MongoDB databases
    _load_sql_databases(neo4j_session, sql_databases, subscription_id, update_tag)
    _load_cassandra_keyspaces(
        neo4j_session, cassandra_keyspaces, subscription_id, update_tag
    )
    _load_mongodb_databases(
        neo4j_session, mongodb_databases, subscription_id, update_tag
    )

    sync_sql_database_details(
        neo4j_session,
        credentials,
        subscription_id,
        sql_databases,
        update_tag,
        common_job_parameters,
    )
    sync_cassandra_keyspace_details(
        neo4j_session,
        credentials,
        subscription_id,
        cassandra_keyspaces,
        update_tag,
        common_job_parameters,
    )
    sync_mongodb_database_details(
        neo4j_session,
        credentials,
        subscription_id,
        mongodb_databases,
        update_tag,
        common_job_parameters,
    )


@timeit
def _load_sql_databases(
    neo4j_session: neo4j.Session,
    sql_databases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest SQL Databases into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBSqlDatabaseSchema(),
        sql_databases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_cassandra_keyspaces(
    neo4j_session: neo4j.Session,
    cassandra_keyspaces: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Cassandra keyspaces into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBCassandraKeyspaceSchema(),
        cassandra_keyspaces,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_mongodb_databases(
    neo4j_session: neo4j.Session,
    mongodb_databases: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest MongoDB databases into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBMongoDBDatabaseSchema(),
        mongodb_databases,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_table_resources(
    neo4j_session: neo4j.Session,
    table_resources: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Table resources into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBTableResourceSchema(),
        table_resources,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_sql_database_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    sql_databases: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    sql_database_details = get_sql_database_details(
        credentials,
        subscription_id,
        sql_databases,
    )
    load_sql_database_details(
        neo4j_session, sql_database_details, subscription_id, update_tag
    )
    cleanup_sql_database_details(neo4j_session, common_job_parameters)


@timeit
def get_sql_database_details(
    credentials: Credentials,
    subscription_id: str,
    sql_databases: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate over the SQL databases to retrieve the SQL containers in them.
    """
    for database in sql_databases:
        containers = get_sql_containers(credentials, subscription_id, database)
        yield database["id"], containers


@timeit
def get_sql_containers(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the list of SQL containers in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        containers = list(
            map(
                lambda x: x.as_dict(),
                client.sql_resources.list_sql_containers(
                    database["resource_group_name"],
                    database["database_account_name"],
                    database["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving SQL containers",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("SQL containers not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving SQL containers list", exc_info=True)
        return []

    return containers


@timeit
def load_sql_database_details(
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionary for SQL Containers
    """
    containers: List[Dict] = []

    for database_id, container in details:
        if len(container) > 0:
            for c in container:
                c["database_id"] = database_id
            containers.extend(container)

    _load_sql_containers(neo4j_session, containers, subscription_id, update_tag)


@timeit
def _load_sql_containers(
    neo4j_session: neo4j.Session,
    containers: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest SQL Container details into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBSqlContainerSchema(),
        containers,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_cassandra_keyspace_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    cassandra_keyspaces: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    cassandra_keyspace_details = get_cassandra_keyspace_details(
        credentials,
        subscription_id,
        cassandra_keyspaces,
    )
    load_cassandra_keyspace_details(
        neo4j_session,
        cassandra_keyspace_details,
        subscription_id,
        update_tag,
    )
    cleanup_cassandra_keyspace_details(neo4j_session, common_job_parameters)


@timeit
def get_cassandra_keyspace_details(
    credentials: Credentials,
    subscription_id: str,
    cassandra_keyspaces: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate through the Cassandra keyspaces to get the list of tables in each keyspace.
    """
    for keyspace in cassandra_keyspaces:
        cassandra_tables = get_cassandra_tables(credentials, subscription_id, keyspace)
        yield keyspace["id"], cassandra_tables


@timeit
def get_cassandra_tables(
    credentials: Credentials,
    subscription_id: str,
    keyspace: Dict,
) -> List[Dict]:
    """
    Returns the list of tables in a Cassandra Keyspace.
    """
    try:
        client = get_client(credentials, subscription_id)
        cassandra_tables = list(
            map(
                lambda x: x.as_dict(),
                client.cassandra_resources.list_cassandra_tables(
                    keyspace["resource_group_name"],
                    keyspace["database_account_name"],
                    keyspace["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving Cassandra tables",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("Cassandra tables not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving Cassandra tables list", exc_info=True)
        return []

    return cassandra_tables


@timeit
def load_cassandra_keyspace_details(
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create a dictionary for Cassandra tables.
    """
    cassandra_tables: List[Dict] = []

    for keyspace_id, cassandra_table in details:
        if len(cassandra_table) > 0:
            for t in cassandra_table:
                t["keyspace_id"] = keyspace_id
            cassandra_tables.extend(cassandra_table)

    _load_cassandra_tables(neo4j_session, cassandra_tables, subscription_id, update_tag)


@timeit
def _load_cassandra_tables(
    neo4j_session: neo4j.Session,
    cassandra_tables: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Cassandra Tables into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBCassandraTableSchema(),
        cassandra_tables,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_mongodb_database_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    mongodb_databases: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    mongodb_databases_details = get_mongodb_databases_details(
        credentials,
        subscription_id,
        mongodb_databases,
    )
    load_mongodb_databases_details(
        neo4j_session, mongodb_databases_details, subscription_id, update_tag
    )
    cleanup_mongodb_database_details(neo4j_session, common_job_parameters)


@timeit
def get_mongodb_databases_details(
    credentials: Credentials,
    subscription_id: str,
    mongodb_databases: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterate through the MongoDB Databases to get the list of collections in each mongoDB database.
    """
    for database in mongodb_databases:
        collections = get_mongodb_collections(credentials, subscription_id, database)
        yield database["id"], collections


@timeit
def get_mongodb_collections(
    credentials: Credentials,
    subscription_id: str,
    database: Dict,
) -> List[Dict]:
    """
    Returns the list of collections in a MongoDB Database.
    """
    try:
        client = get_client(credentials, subscription_id)
        collections = list(
            map(
                lambda x: x.as_dict(),
                client.mongo_db_resources.list_mongo_db_collections(
                    database["resource_group_name"],
                    database["database_account_name"],
                    database["name"],
                ),
            ),
        )

    except ClientAuthenticationError:
        logger.warning(
            "Client Authentication Error while retrieving MongoDB collections",
            exc_info=True,
        )
        return []
    except ResourceNotFoundError:
        logger.warning("MongoDB collections not found error", exc_info=True)
        return []
    except HttpResponseError:
        logger.warning("Error while retrieving MongoDB collections list", exc_info=True)
        return []

    return collections


@timeit
def load_mongodb_databases_details(
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create a dictionary for MongoDB tables.
    """
    collections: List[Dict] = []

    for database_id, collection in details:
        if len(collection) > 0:
            for c in collection:
                c["database_id"] = database_id
            collections.extend(collection)

    _load_collections(neo4j_session, collections, subscription_id, update_tag)


@timeit
def _load_collections(
    neo4j_session: neo4j.Session,
    collections: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest MongoDB Collections into neo4j.
    """
    load(
        neo4j_session,
        AzureCosmosDBMongoDBCollectionSchema(),
        collections,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_azure_database_accounts(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(AzureCosmosDBAccountSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AzureCosmosDBLocationSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCosmosDBCorsPolicySchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCosmosDBVirtualNetworkRuleSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCDBPrivateEndpointConnectionSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def cleanup_sql_database_details(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        AzureCosmosDBSqlContainerSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCosmosDBSqlDatabaseSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def cleanup_cassandra_keyspace_details(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        AzureCosmosDBCassandraTableSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCosmosDBCassandraKeyspaceSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def cleanup_mongodb_database_details(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        AzureCosmosDBMongoDBCollectionSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        AzureCosmosDBMongoDBDatabaseSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def cleanup_table_resources(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        AzureCosmosDBTableResourceSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    sync_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure CosmosDB for subscription '%s'.", subscription_id)
    database_account_list = get_database_account_list(credentials, subscription_id)
    database_account_list = transform_database_account_data(database_account_list)
    load_database_account_data(
        neo4j_session,
        subscription_id,
        database_account_list,
        sync_tag,
    )
    sync_database_account_data_resources(
        neo4j_session,
        subscription_id,
        database_account_list,
        sync_tag,
    )
    sync_database_account_details(
        neo4j_session,
        credentials,
        subscription_id,
        database_account_list,
        sync_tag,
        common_job_parameters,
    )
    cleanup_azure_database_accounts(neo4j_session, common_job_parameters)
