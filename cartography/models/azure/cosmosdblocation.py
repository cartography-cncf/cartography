if (
        "write_locations" in database_account
        and len(database_account["write_locations"]) > 0
    ):
        database_account_id = database_account["id"]
        write_locations = database_account["write_locations"]

        ingest_write_location = """
        UNWIND $write_locations_list as wl
        MERGE (loc:AzureCosmosDBLocation{id: wl.id})
        ON CREATE SET loc.firstseen = timestamp()
        SET loc.lastupdated = $azure_update_tag,
        loc.locationname = wl.location_name,
        loc.documentendpoint = wl.document_endpoint,
        loc.provisioningstate = wl.provisioning_state,
        loc.failoverpriority = wl.failover_priority,
        loc.iszoneredundant = wl.is_zone_redundant
        WITH loc
        MATCH (d:AzureCosmosDBAccount{id: $DatabaseAccountId})
        MERGE (d)-[r:CAN_WRITE_FROM]->(loc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $azure_update_tag
        """

        neo4j_session.run(
            ingest_write_location,
            write_locations_list=write_locations,
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )

    """
    Ingest the details of location with read permission enabled.
    """
    if (
        "read_locations" in database_account
        and len(database_account["read_locations"]) > 0
    ):
        database_account_id = database_account["id"]
        read_locations = database_account["read_locations"]

        ingest_read_location = """
        UNWIND $read_locations_list as rl
        MERGE (loc:AzureCosmosDBLocation{id: rl.id})
        ON CREATE SET loc.firstseen = timestamp()
        SET loc.lastupdated = $azure_update_tag,
        loc.locationname = rl.location_name,
        loc.documentendpoint = rl.document_endpoint,
        loc.provisioningstate = rl.provisioning_state,
        loc.failoverpriority = rl.failover_priority,
        loc.iszoneredundant = rl.is_zone_redundant
        WITH loc
        MATCH (d:AzureCosmosDBAccount{id: $DatabaseAccountId})
        MERGE (d)-[r:CAN_READ_FROM]->(loc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $azure_update_tag
        """

        neo4j_session.run(
            ingest_read_location,
            read_locations_list=read_locations,
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )

    """
    Ingest the details of enabled location for the database account.
    """
    if "locations" in database_account and len(database_account["locations"]) > 0:
        database_account_id = database_account["id"]
        associated_locations = database_account["locations"]

        ingest_associated_location = """
        UNWIND $associated_locations_list as al
        MERGE (loc:AzureCosmosDBLocation{id: al.id})
        ON CREATE SET loc.firstseen = timestamp()
        SET loc.lastupdated = $azure_update_tag,
        loc.locationname = al.location_name,
        loc.documentendpoint = al.document_endpoint,
        loc.provisioningstate = al.provisioning_state,
        loc.failoverpriority = al.failover_priority,
        loc.iszoneredundant = al.is_zone_redundant
        WITH loc
        MATCH (d:AzureCosmosDBAccount{id: $DatabaseAccountId})
        MERGE (d)-[r:ASSOCIATED_WITH]->(loc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $azure_update_tag
        """

        neo4j_session.run(
            ingest_associated_location,
            associated_locations_list=associated_locations,
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )
