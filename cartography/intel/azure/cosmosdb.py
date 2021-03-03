import logging
import uuid
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from cartography.util import get_optional_value
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(credentials, subscription_id):
    """
    Getting the CosmosDB client
    """
    client = CosmosDBManagementClient(credentials, subscription_id)
    return client


@timeit
def get_database_account_list(credentials, subscription_id):
    """
    Get a list of all database accounts.
    """
    try:
        client = get_client(credentials, subscription_id)
        database_account_list = list(map(lambda x: x.as_dict(), client.database_accounts.list()))

    except Exception as e:
        logger.warning("Error while retrieving database accounts - {}".format(e))
        return []

    for database_account in database_account_list:
        x = database_account['id'].split('/')
        database_account['resourceGroup'] = x[x.index('resourceGroups')+1]

    return database_account_list


@timeit
def load_database_account_data(neo4j_session, subscription_id, database_account_list, azure_update_tag):
    """
    Ingest data of all database accounts into neo4j.
    """
    ingest_database_account = """
    UNWIND {database_accounts_list} AS da
    MERGE (d:AzureDatabaseAccount{id: da.id})
    ON CREATE SET d.firstseen = timestamp(),
    d.name = da.name, d.resourcegroup = da.resourceGroup,
    d.location = da.location
    SET d.lastupdated = {azure_update_tag},
    d.kind = da.kind,
    d.type = da.type,
    d.ipranges = da.ipruleslist,
    d.capabilities = da.list_of_capabilities,
    d.documentendpoint = da.document_endpoint,
    d.virtualnetworkfilterenabled = da.is_virtual_network_filter_enabled,
    d.enableautomaticfailover = da.enable_automatic_failover,
    d.provisioningstate = da.provisioning_state,
    d.multiplewritelocations = da.enable_multiple_write_locations,
    d.accountoffertype = da.database_account_offer_type,
    d.publicnetworkaccess = da.public_network_access,
    d.enablecassandraconnector = da.enable_cassandra_connector,
    d.connectoroffer = da.connector_offer,
    d.disablekeybasedmetadatawriteaccess = da.disable_key_based_metadata_write_access,
    d.keyvaulturi = da.key_vault_key_uri,
    d.enablefreetier = da.enable_free_tier,
    d.enableanalyticalstorage = da.enable_analytical_storage,
    d.defaultconsistencylevel = da.consistency_policy.default_consistency_level,
    d.maxstalenessprefix = da.consistency_policy.max_staleness_prefix,
    d.maxintervalinseconds = da.consistency_policy.max_interval_in_seconds
    WITH d
    MATCH (owner:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for database_account in database_account_list:
        capabilities = []
        iprules = []
        if 'capabilities' in database_account and len(database_account['capabilities']) > 0:
            capabilities = [x['name'] for x in database_account['capabilities']]
        if 'ip_rules' in database_account and len(database_account['ip_rules']) > 0:
            iprules = [x['ip_address_or_range'] for x in database_account['ip_rules']]
        database_account['ipruleslist'] = iprules
        database_account['list_of_capabilities'] = capabilities

    neo4j_session.run(
        ingest_database_account,
        database_accounts_list=database_account_list,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )

    for database_account in database_account_list:
        # cleanup existing cors policy properties
        run_cleanup_job(
            'azure_cosmosdb_cors_details.json',
            neo4j_session,
            {'UPDATE_TAG': azure_update_tag, 'AZURE_SUBSCRIPTION_ID': subscription_id},
        )

        if 'cors' in database_account and len(database_account['cors']) > 0:
            _load_cosmosdb_cors_policy(neo4j_session, database_account, azure_update_tag)
        if 'failover_policies' in database_account and len(database_account['failover_policies']) > 0:
            _load_cosmosdb_failover_policies(neo4j_session, database_account, azure_update_tag)
        if 'private_endpoint_connections' in database_account and len(database_account['private_endpoint_connections']) > 0:
            _load_cosmosdb_private_endpoint_connections(neo4j_session, database_account, azure_update_tag)
        if 'virtual_network_rules' in database_account and len(database_account['virtual_network_rules']) > 0:
            _load_cosmosdb_virtual_network_rules(neo4j_session, database_account, azure_update_tag)

        locations = []
        # Extracting every location
        if 'write_locations' in database_account and len(database_account['write_locations']) > 0:
            for loc in database_account['write_locations']:
                locations.append(loc)
        if 'read_locations' in database_account and len(database_account['read_locations']) > 0:
            for loc in database_account['read_locations']:
                locations.append(loc)
        if 'locations' in database_account and len(database_account['locations']) > 0:
            for loc in database_account['locations']:
                locations.append(loc)
        loc = [i for n, i in enumerate(locations) if i not in locations[n + 1:]]  # Selecting only the unique location entries
        if len(loc) > 0:
            _load_database_account_locations(neo4j_session, database_account, loc, azure_update_tag)


@timeit
def _load_database_account_locations(neo4j_session, database_account, locations, azure_update_tag):
    """
    Getting locations enabled with read/write permissions for the database account.
    """
    database_account_id = database_account['id']
    for loc in locations:
        if 'write_locations' in database_account and loc in database_account['write_locations']:
            _load_database_account_write_locations(neo4j_session, database_account_id, loc, azure_update_tag)
        if 'read_locations' in database_account and loc in database_account['read_locations']:
            _load_database_account_read_locations(neo4j_session, database_account_id, loc, azure_update_tag)
        if 'locations' in database_account and loc in database_account['locations']:
            _load_database_account_associated_locations(neo4j_session, database_account_id, loc, azure_update_tag)


@timeit
def _load_database_account_write_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of location with write permission enabled.
    """
    ingest_write_location = """
    MERGE (loc:AzureCosmosDBLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:WRITE_PERMISSIONS_FROM]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_write_location,
        LocationId=loc['id'],
        Name=loc['location_name'],
        DocumentEndpoint=loc['document_endpoint'],
        ProvisioningState=loc['provisioning_state'],
        FailoverPriority=loc['failover_priority'],
        IsZoneRedundant=loc['is_zone_redundant'],
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_database_account_read_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of location with read permission enabled.
    """
    ingest_read_location = """
    MERGE (loc:AzureCosmosDBLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:READ_PERMISSIONS_FROM]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_read_location,
        LocationId=loc['id'],
        Name=loc['location_name'],
        DocumentEndpoint=loc['document_endpoint'],
        ProvisioningState=loc['provisioning_state'],
        FailoverPriority=loc['failover_priority'],
        IsZoneRedundant=loc['is_zone_redundant'],
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_database_account_associated_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of enabled location for the database account.
    """
    ingest_associated_location = """
    MERGE (loc:AzureCosmosDBLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:ASSOCIATED_WITH]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_associated_location,
        LocationId=loc['id'],
        Name=loc['location_name'],
        DocumentEndpoint=loc['document_endpoint'],
        ProvisioningState=loc['provisioning_state'],
        FailoverPriority=loc['failover_priority'],
        IsZoneRedundant=loc['is_zone_redundant'],
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_cosmosdb_cors_policy(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Cors Policy of the database account.
    """
    database_account_id = database_account['id']
    cors_policies = database_account['cors']

    ingest_cors_policy = """
    UNWIND {cors_policies_list} AS cp
    MERGE (corspolicy:AzureCosmosDBCorsPolicy{id: cp.cors_policy_unique_id})
    ON CREATE SET corspolicy.firstseen = timestamp(), 
    corspolicy.allowedorigins = cp.allowed_origins
    SET corspolicy.lastupdated = {azure_update_tag},
    corspolicy.allowedmethods = cp.allowed_methods,
    corspolicy.allowedheaders = cp.allowed_headers,
    corspolicy.exposedheaders = cp.exposed_headers,
    corspolicy.maxageinseconds = cp.max_age_in_seconds
    WITH corspolicy
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(corspolicy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for policy in cors_policies:
        policy['cors_policy_unique_id'] = uuid.uuid4()

    neo4j_session.run(
        ingest_cors_policy,
        cors_policies_list=cors_policies,
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_cosmosdb_failover_policies(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Failover Policies of the database account.
    """
    database_account_id = database_account['id']
    failover_policies = database_account['failover_policies']

    ingest_failover_policies = """
    UNWIND {failover_policies_list} AS fp
    MERGE (fpolicy:AzureDatabaseAccountFailoverPolicy{id: fp.id})
    ON CREATE SET fpolicy.firstseen = timestamp()
    SET fpolicy.lastupdated = {azure_update_tag},
    fpolicy.locationname = fp.location_name,
    fpolicy.failoverpriority = fp.failover_priority
    WITH fpolicy
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(fpolicy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_failover_policies,
        failover_policies_list=failover_policies,
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_cosmosdb_private_endpoint_connections(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Private Endpoint Connections of the database account.
    """
    database_account_id = database_account['id']
    private_endpoint_connections = database_account['private_endpoint_connections']

    ingest_private_endpoint_connections = """
    UNWIND {private_endpoint_connections_list} AS connection
    MERGE (pec:AzureCosmosDBPrivateEndpointConnection{id: connection.id})
    ON CREATE SET pec.firstseen = timestamp()
    SET pec.lastupdated = {azure_update_tag},
    pec.name = connection.name,
    pec.privateendpointid = connection.{PrivateEndpointId},
    pec.status = connection.private_link_service_connection_state.status,
    pec.actionrequired = connection.private_link_service_connection_state.actions_required
    WITH pec
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONFIGURED_WITH]->(pec)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_private_endpoint_connections,
        private_endpoint_connections_list=private_endpoint_connections,
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_cosmosdb_virtual_network_rules(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Virtual Network Rules of the database account.
    """
    database_account_id = database_account['id']
    virtual_network_rules = database_account['virtual_network_rules']

    ingest_virtual_network_rules = """
    UNWIND {virtual_network_rules_list} AS vnr
    MERGE (rules:AzureCosmosDBVirtualNetworkRule{id: vnr.id})
    ON CREATE SET rules.firstseen = timestamp()
    SET rules.lastupdated = {azure_update_tag},
    rules.ignoremissingvnetserviceendpoint = vnr.ignore_missing_v_net_service_endpoint
    WITH rules
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONFIGURED_WITH]->(rules)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_virtual_network_rules,
        virtual_network_rules_list=virtual_network_rules,
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def sync_database_account_details(neo4j_session, credentials, subscription_id, database_account_list, sync_tag, common_job_parameters):
    details = get_database_account_details(credentials, subscription_id, database_account_list)
    load_database_account_details(neo4j_session, credentials, subscription_id, details, sync_tag, common_job_parameters)


@timeit
def get_database_account_details(credentials, subscription_id, database_account_list):
    """
    Iterate over the database accounts and return the list of SQL and MongoDB databases, Cassandra keyspaces and table resources associated with each database account.
    """
    for database_account in database_account_list:
        sql_databases = get_sql_databases(credentials, subscription_id, database_account)
        cassandra_keyspaces = get_cassandra_keyspaces(credentials, subscription_id, database_account)
        mongodb_databases = get_mongodb_databases(credentials, subscription_id, database_account)
        table_resources = get_table_resources(credentials, subscription_id, database_account)
        yield database_account['id'], database_account['name'], database_account['resourceGroup'], sql_databases, cassandra_keyspaces, mongodb_databases, table_resources


@timeit
def get_sql_databases(credentials, subscription_id, database_account):
    """
    Return the list of SQL Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        sql_database_list = list(map(lambda x: x.as_dict(), client.sql_resources.list_sql_databases(database_account['resourceGroup'], database_account['name'])))

    except Exception as e:
        logger.warning("Error while retrieving SQL Database list - {}".format(e))
        return []

    return sql_database_list


@timeit
def get_cassandra_keyspaces(credentials, subscription_id, database_account):
    """
    Return the list of Cassandra Keyspaces in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        cassandra_keyspace_list = list(map(lambda x: x.as_dict(), client.cassandra_resources.list_cassandra_keyspaces(database_account['resourceGroup'], database_account['name'])))

    except Exception as e:
        logger.warning("Error while retrieving Cassandra keyspaces list - {}".format(e))
        return []

    return cassandra_keyspace_list


@timeit
def get_mongodb_databases(credentials, subscription_id, database_account):
    """
    Return the list of MongoDB Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        mongodb_database_list = list(map(lambda x: x.as_dict(), client.mongo_db_resources.list_mongo_db_databases(database_account['resourceGroup'], database_account['name'])))

    except Exception as e:
        logger.warning("Error while retrieving MongoDB Database list - {}".format(e))
        return []

    return mongodb_database_list


@timeit
def get_table_resources(credentials, subscription_id, database_account):
    """
    Return the list of Table Resources in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        table_resources_list = list(map(lambda x: x.as_dict(), client.table_resources.list_tables(database_account['resourceGroup'], database_account['name'])))

    except Exception as e:
        logger.warning("Error while retrieving table resources list - {}".format(e))
        return []

    return table_resources_list


@timeit
def load_database_account_details(neo4j_session, credentials, subscription_id, details, update_tag, common_job_parameters):
    """
    Create dictionaries for SQL Databases, Cassandra Keyspaces, MongoDB Databases and table resources.
    """
    sql_databases = []
    cassandra_keyspaces = []
    mongodb_databases = []
    table_resources = []

    for account_id, name, resourceGroup, sql_database, cassandra_keyspace, mongodb_database, table in details:
        if len(sql_database) > 0:
            for db in sql_database:
                db['database_account_name'] = name
                db['database_account_id'] = account_id
                db['resource_group_name'] = resourceGroup
            sql_databases.extend(sql_database)

        if len(cassandra_keyspace) > 0:
            for keyspace in cassandra_keyspace:
                keyspace['database_account_name'] = name
                keyspace['database_account_id'] = account_id
                keyspace['resource_group_name'] = resourceGroup
            cassandra_keyspaces.extend(cassandra_keyspace)

        if len(mongodb_database) > 0:
            for db in mongodb_database:
                db['database_account_name'] = name
                db['database_account_id'] = account_id
                db['resource_group_name'] = resourceGroup
            mongodb_databases.extend(mongodb_database)

        if len(table) > 0:
            for t in table:
                t['database_account_id'] = account_id
            table_resources.extend(table)

    _load_table_resources(neo4j_session, table_resources, update_tag)
    cleanup_table_resources(neo4j_session, subscription_id, common_job_parameters)

    _load_sql_databases(neo4j_session, sql_databases, update_tag)
    _load_cassandra_keyspaces(neo4j_session, cassandra_keyspaces, update_tag)
    _load_mongodb_databases(neo4j_session, mongodb_databases, update_tag)

    sync_sql_database_details(neo4j_session, credentials, subscription_id, sql_databases, update_tag, common_job_parameters)
    sync_cassandra_keyspace_details(neo4j_session, credentials, subscription_id, cassandra_keyspaces, update_tag, common_job_parameters)
    sync_mongodb_database_details(neo4j_session, credentials, subscription_id, mongodb_databases, update_tag, common_job_parameters)


@timeit
def _load_sql_databases(neo4j_session, sql_databases, update_tag):
    """
    Ingest SQL Databases into neo4j.
    """
    ingest_sql_databases = """
    UNWIND {sql_databases_list} AS database
    MERGE (sdb:AzureCosmosDBSqlDatabase{id: database.id})
    ON CREATE SET sdb.firstseen = timestamp(), sdb.lastupdated = {azure_update_tag}
    SET sdb.name = database.name,
    sdb.type = database.type,
    sdb.location = database.location,
    sdb.throughput = database.options.throughput,
    sdb.maxthroughput = database.options.autoscale_setting.max_throughput
    WITH sdb, database
    MATCH (d:AzureDatabaseAccount{id: database.database_account_id})
    MERGE (d)-[r:CONTAINS]->(sdb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_sql_databases,
        sql_databases_list=sql_databases,
        azure_update_tag=update_tag,
    )


@timeit
def _load_cassandra_keyspaces(neo4j_session, cassandra_keyspaces, update_tag):
    """
    Ingest Cassandra keyspaces into neo4j.
    """
    ingest_cassandra_keyspaces = """
    UNWIND {cassandra_keyspaces_list} AS keyspace
    MERGE (ck:AzureCosmosDBCassandraKeyspace{id: keyspace.id})
    ON CREATE SET ck.firstseen = timestamp(), ck.lastupdated = {azure_update_tag}
    SET ck.name = keyspace.name,
    ck.type = keyspace.type,
    ck.location = keyspace.location,
    ck.throughput = keyspace.options.throughput,
    ck.maxthroughput = keyspace.options.autoscale_setting.max_throughput
    WITH ck, keyspace
    MATCH (d:AzureDatabaseAccount{id: keyspace.database_account_id})
    MERGE (d)-[r:CONTAINS]->(ck)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_cassandra_keyspaces,
        cassandra_keyspaces_list=cassandra_keyspaces,
        azure_update_tag=update_tag,
    )


@timeit
def _load_mongodb_databases(neo4j_session, mongodb_databases, update_tag):
    """
    Ingest MongoDB databases into neo4j.
    """
    ingest_mongodb_databases = """
    UNWIND {mongodb_databases_list} AS database
    MERGE (mdb:AzureCosmosDBMongoDBDatabase{id: database.id})
    ON CREATE SET mdb.firstseen = timestamp(), mdb.lastupdated = {azure_update_tag}
    SET mdb.name = database.name,
    mdb.type = database.type,
    mdb.location = database.location,
    mdb.throughput = database.options.throughput,
    mdb.maxthroughput = database..options.autoscale_setting.max_throughput
    WITH mdb, database
    MATCH (d:AzureDatabaseAccount{id: database.database_account_id})
    MERGE (d)-[r:CONTAINS]->(mdb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_mongodb_databases,
        mongodb_databases_list=mongodb_databases,
        azure_update_tag=update_tag,
    )


@timeit
def _load_table_resources(neo4j_session, table_resources, update_tag):
    """
    Ingest Table resources into neo4j.
    """
    ingest_tables = """
    UNWIND {table_resources_list} AS table
    MERGE (tr:AzureCosmosDBTableResource{id: table.id})
    ON CREATE SET tr.firstseen = timestamp(), tr.lastupdated = {azure_update_tag}
    SET tr.name = table.name,
    tr.type = table.type,
    tr.location = table.location,
    tr.throughput = table.options.throughput,
    tr.maxthroughput = table.options.autoscale_setting.max_throughput
    WITH tr, table
    MATCH (d:AzureDatabaseAccount{id: table.database_account_id})
    MERGE (d)-[r:CONTAINS]->(tr)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_tables,
        table_resources_list=table_resources,
        azure_update_tag=update_tag,
    )


@timeit
def sync_sql_database_details(neo4j_session, credentials, subscription_id, sql_databases, update_tag, common_job_parameters):
    sql_database_details = get_sql_database_details(credentials, subscription_id, sql_databases)
    load_sql_database_details(neo4j_session, sql_database_details, update_tag)
    cleanup_sql_database_details(neo4j_session, subscription_id, common_job_parameters)


@timeit
def get_sql_database_details(credentials, subscription_id, sql_databases):
    """
    Iterate over the SQL databases to retrieve the SQL containers in them.
    """
    for database in sql_databases:
        containers = get_sql_containers(credentials, subscription_id, database)
        yield database['id'], containers


@timeit
def get_sql_containers(credentials, subscription_id, database):
    """
    Returns the list of SQL containers in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        containers = list(map(lambda x: x.as_dict(), client.sql_resources.list_sql_containers(database['resource_group_name'], database['database_account_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving SQL Containers - {}".format(e))
        return []

    return containers


@timeit
def load_sql_database_details(neo4j_session, details, update_tag):
    """
    Create dictionary for SQL Containers
    """
    containers = []

    for database_id, container in details:
        if len(container) > 0:
            for c in container:
                c['database_id'] = database_id
            containers.extend(container)

    _load_sql_containers(neo4j_session, containers, update_tag)


@timeit
def _load_sql_containers(neo4j_session, containers, update_tag):
    """
    Ingest SQL Container details into neo4j.
    """
    ingest_containers = """
    UNWIND {sql_containers_list} AS container
    MERGE (c:AzureCosmosDBSqlContainer{id: container.id})
    ON CREATE SET c.firstseen = timestamp(), c.lastupdated = {azure_update_tag}
    SET c.name = container.name,
    c.type = container.type,
    c.location = container.location,
    c.throughput = container.options.throughput,
    c.maxthroughput = container.options.autoscale_setting.max_throughput,
    c.container = container.resource.id,
    c.defaultttl = container.resource.default_ttl,
    c.analyticalttl = container.resource.analytical_storage_ttl,
    c.isautomaticindexingpolicy = container.resource.indexing_policy.automatic,
    c.indexingmode = container.resource.indexing_policy.indexing_mode,
    c.conflictresolutionpolicymode = container.resource.conflict_resolution_policy.mode
    WITH c, container
    MATCH (sdb:AzureCosmosDBSqlDatabase{id: container.database_id})
    MERGE (sdb)-[r:CONTAINS]->(c)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_containers,
        sql_containers_list=containers,
        azure_update_tag=update_tag,
    )


@timeit
def sync_cassandra_keyspace_details(neo4j_session, credentials, subscription_id, cassandra_keyspaces, update_tag, common_job_parameters):
    cassandra_keyspace_details = get_cassandra_keyspace_details(credentials, subscription_id, cassandra_keyspaces)
    load_cassandra_keyspace_details(neo4j_session, cassandra_keyspace_details, update_tag)
    cleanup_cassandra_keyspace_details(neo4j_session, subscription_id, common_job_parameters)


@timeit
def get_cassandra_keyspace_details(credentials, subscription_id, cassandra_keyspaces):
    """
    Iterate through the Cassandra keyspaces to get the list of tables in each keyspace.
    """
    for keyspace in cassandra_keyspaces:
        cassandra_tables = get_cassandra_tables(credentials, subscription_id, keyspace)
        yield keyspace['id'], cassandra_tables


@timeit
def get_cassandra_tables(credentials, subscription_id, keyspace):
    """
    Returns the list of tables in a Cassandra Keyspace.
    """
    try:
        client = get_client(credentials, subscription_id)
        cassandra_tables = list(map(lambda x: x.as_dict(), client.cassandra_resources.list_cassandra_tables(keyspace['resource_group_name'], keyspace['database_account_name'], keyspace['name'])))

    except Exception as e:
        logger.warning("Error while retrieving Cassandra tables - {}".format(e))
        return []

    return cassandra_tables


@timeit
def load_cassandra_keyspace_details(neo4j_session, details, update_tag):
    """
    Create a dictionary for Cassandra tables.
    """
    cassandra_tables = []

    for keyspace_id, cassandra_table in details:
        if len(cassandra_table) > 0:
            for t in cassandra_table:
                t['keyspace_id'] = keyspace_id
            cassandra_tables.extend(cassandra_table)

    _load_cassandra_tables(neo4j_session, cassandra_tables, update_tag)


@timeit
def _load_cassandra_tables(neo4j_session, cassandra_tables, update_tag):
    """
    Ingest Cassandra Tables into neo4j.
    """
    ingest_cassandra_tables = """
    UNWIND {cassandra_tables_list} AS table
    MERGE (ct:AzureCosmosDBCassandraTable{id: table.{ResourceId}})
    ON CREATE SET ct.firstseen = timestamp(), ct.lastupdated = {azure_update_tag}
    SET ct.name = table.name,
    ct.type = table.type,
    ct.location = table.location,
    ct.throughput = table.options.throughput,
    ct.maxthroughput = table.options.autoscale_setting.max_throughput,
    ct.container = table.resource.id,
    ct.defaultttl = table.resource.default_ttl,
    ct.analyticalttl = table.resource.analytical_storage_ttl
    WITH ct, table
    MATCH (ck:AzureCosmosDBCassandraKeyspace{id: table.keyspace_id})
    MERGE (ck)-[r:CONTAINS]->(ct)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_cassandra_tables,
        cassandra_tables_list=cassandra_tables,
        azure_update_tag=update_tag,
    )


@timeit
def sync_mongodb_database_details(neo4j_session, credentials, subscription_id, mongodb_databases, update_tag, common_job_parameters):
    mongodb_databases_details = get_mongodb_databases_details(credentials, subscription_id, mongodb_databases)
    load_mongodb_databases_details(neo4j_session, mongodb_databases_details, update_tag)
    cleanup_mongodb_database_details(neo4j_session, subscription_id, common_job_parameters)


@timeit
def get_mongodb_databases_details(credentials, subscription_id, mongodb_databases):
    """
    Iterate through the MongoDB Databases to get the list of collections in each mongoDB database.
    """
    for database in mongodb_databases:
        collections = get_mongodb_collections(credentials, subscription_id, database)
        yield database['id'], collections


@timeit
def get_mongodb_collections(credentials, subscription_id, database):
    """
    Returns the list of collections in a MongoDB Database.
    """
    try:
        client = get_client(credentials, subscription_id)
        collections = list(map(lambda x: x.as_dict(), client.mongo_db_resources.list_mongo_db_collections(database['resource_group_name'], database['database_account_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving MongoDB collections - {}".format(e))
        return []

    return collections


@timeit
def load_mongodb_databases_details(neo4j_session, details, update_tag):
    """
    Create a dictionary for MongoDB tables.
    """
    collections = []

    for database_id, collection in details:
        if len(collection) > 0:
            for c in collection:
                c['database_id'] = database_id
            collections.extend(collection)

    _load_collections(neo4j_session, collections, update_tag)


@timeit
def _load_collections(neo4j_session, collections, update_tag):
    """
    Ingest MongoDB Collections into neo4j.
    """
    ingest_collections = """
    UNWIND {mongodb_collections_list} AS collection
    MERGE (col:AzureCosmosDBMongoDBCollection{id: collection.id})
    ON CREATE SET col.firstseen = timestamp(), col.lastupdated = {azure_update_tag}
    SET col.name = collection.name,
    col.type = collection.type,
    col.location = collection.location,
    col.throughput = collection.options.throughput,
    col.maxthroughput = collection.options.autoscale_setting.max_throughput,
    col.collectionname = collection.resource.id,
    col.analyticalttl = collection.resource.analytical_storage_ttl
    WITH col, collection
    MATCH (mdb:AzureCosmosDBMongoDBDatabase{id: collection.database_id})
    MERGE (mdb)-[r:CONTAINS]->(col)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for collection in collections:
        neo4j_session.run(
            ingest_collections,
            ResourceId=collection['id'],
            Name=collection['name'],
            Type=collection['type'],
            Location=get_optional_value(collection, ['location']),
            Throughput=get_optional_value(collection, ['options', 'throughput']),
            MaxThroughput=get_optional_value(collection, ['options', 'autoscale_setting', 'max_throughput']),
            CollectionName=get_optional_value(collection, ['resource', 'id']),
            AnalyticalTTL=get_optional_value(collection, ['resource', 'analytical_storage_ttl']),
            DatabaseId=collection['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def cleanup_azure_database_accounts(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_database_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_sql_database_details(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_cosmosdb_sql_database_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_cassandra_keyspace_details(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_cosmosdb_cassandra_keyspace_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_mongodb_database_details(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_cosmosdb_mongodb_database_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_table_resources(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_cosmosdb_table_resources_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure CosmosDB for subscription '%s'.", subscription_id)
    database_account_list = get_database_account_list(credentials, subscription_id)
    load_database_account_data(neo4j_session, subscription_id, database_account_list, sync_tag)
    sync_database_account_details(neo4j_session, credentials, subscription_id, database_account_list, sync_tag, common_job_parameters)
    cleanup_azure_database_accounts(neo4j_session, subscription_id, common_job_parameters)
