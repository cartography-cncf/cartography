from unittest.mock import patch

import cartography.intel.azure.sql
from tests.data.azure.sql import DESCRIBE_AD_ADMINS
from tests.data.azure.sql import DESCRIBE_DATABASES
from tests.data.azure.sql import DESCRIBE_DNS_ALIASES
from tests.data.azure.sql import DESCRIBE_ELASTIC_POOLS
from tests.data.azure.sql import DESCRIBE_FAILOVER_GROUPS
from tests.data.azure.sql import DESCRIBE_RECOVERABLE_DATABASES
from tests.data.azure.sql import DESCRIBE_REPLICATION_LINKS
from tests.data.azure.sql import DESCRIBE_RESTORABLE_DROPPED_DATABASES
from tests.data.azure.sql import DESCRIBE_RESTORE_POINTS
from tests.data.azure.sql import DESCRIBE_SERVERS
from tests.data.azure.sql import DESCRIBE_THREAT_DETECTION_POLICY
from tests.data.azure.sql import DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP = "TestRG"
TEST_UPDATE_TAG = 123456789
server1 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1"
server2 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2"


@patch.object(
    cartography.intel.azure.sql,
    "get_transparent_data_encryptions",
    side_effect=lambda creds, sub_id, db: next(
        (
            tde
            for tde in DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS
            if tde["database_id"] == db["id"]
        ),
        {},
    ),
)
@patch.object(
    cartography.intel.azure.sql,
    "get_restore_points",
    side_effect=lambda creds, sub_id, db: [
        rp for rp in DESCRIBE_RESTORE_POINTS if rp["database_id"] == db["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_db_threat_detection_policies",
    side_effect=lambda creds, sub_id, db: next(
        (
            tdp
            for tdp in DESCRIBE_THREAT_DETECTION_POLICY
            if tdp["database_id"] == db["id"]
        ),
        {},
    ),
)
@patch.object(
    cartography.intel.azure.sql,
    "get_replication_links",
    side_effect=lambda creds, sub_id, db: [
        rl for rl in DESCRIBE_REPLICATION_LINKS if rl["database_id"] == db["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_databases",
    side_effect=lambda creds, sub_id, server: [
        db for db in DESCRIBE_DATABASES if db["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_elastic_pools",
    side_effect=lambda creds, sub_id, server: [
        ep for ep in DESCRIBE_ELASTIC_POOLS if ep["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_failover_groups",
    side_effect=lambda creds, sub_id, server: [
        fg for fg in DESCRIBE_FAILOVER_GROUPS if fg["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_restorable_dropped_databases",
    side_effect=lambda creds, sub_id, server: [
        rdd
        for rdd in DESCRIBE_RESTORABLE_DROPPED_DATABASES
        if rdd["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_recoverable_databases",
    side_effect=lambda creds, sub_id, server: [
        rd for rd in DESCRIBE_RECOVERABLE_DATABASES if rd["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_ad_admins",
    side_effect=lambda creds, sub_id, server: [
        admin for admin in DESCRIBE_AD_ADMINS if admin["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_dns_aliases",
    side_effect=lambda creds, sub_id, server: [
        alias for alias in DESCRIBE_DNS_ALIASES if alias["server_id"] == server["id"]
    ],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_server_list",
    return_value=DESCRIBE_SERVERS,
)
def test_sync_sql_servers_and_databases(
    mock_get_servers,
    mock_get_dns_aliases,
    mock_get_ad_admins,
    mock_get_recoverable_dbs,
    mock_get_restorable_dropped_dbs,
    mock_get_failover_groups,
    mock_get_elastic_pools,
    mock_get_databases,
    mock_get_replication_links,
    mock_get_threat_detection,
    mock_get_restore_points,
    mock_get_tde,
    neo4j_session,
):
    """
    Test that SQL servers and all nested resources sync correctly via the main sync() function.
    Tests servers, databases, DNS aliases, AD admins, recoverable databases, restorable dropped databases,
    failover groups, elastic pools, replication links, threat detection policies, restore points,
    and transparent data encryptions.
    """
    # Arrange - Create subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Call main sync function
    cartography.intel.azure.sql.sync(
        neo4j_session,
        credentials=None,  # Mocked
        subscription_id=TEST_SUBSCRIPTION_ID,
        sync_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        },
    )

    # Assert - Check SQL servers exist
    expected_server_nodes = {
        (server1,),
        (server2,),
    }
    assert check_nodes(neo4j_session, "AzureSQLServer", ["id"]) == expected_server_nodes

    # Assert - Check databases exist
    expected_database_nodes = {
        (server1 + "/databases/testdb1",),
        (server2 + "/databases/testdb2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureSQLDatabase", ["id"])
        == expected_database_nodes
    )

    # Assert - Check server-to-subscription relationships
    expected_server_rels = {
        (TEST_SUBSCRIPTION_ID, server1),
        (TEST_SUBSCRIPTION_ID, server2),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSQLServer",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_server_rels
    )

    # Assert - Check server-to-database relationships
    expected_db_rels = {
        (server1, server1 + "/databases/testdb1"),
        (server2, server2 + "/databases/testdb2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureSQLDatabase",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_db_rels
    )

    # Assert - Check DNS aliases exist
    expected_dns_alias_nodes = {
        (server1 + "/dnsAliases/dns-alias-1",),
        (server2 + "/dnsAliases/dns-alias-2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureServerDNSAlias", ["id"])
        == expected_dns_alias_nodes
    )

    # Assert - Check server-to-DNS alias relationships
    expected_dns_alias_rels = {
        (server1, server1 + "/dnsAliases/dns-alias-1"),
        (server2, server2 + "/dnsAliases/dns-alias-2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureServerDNSAlias",
            "id",
            "USED_BY",
            rel_direction_right=True,
        )
        == expected_dns_alias_rels
    )

    # Assert - Check AD admins exist
    expected_ad_admin_nodes = {
        (server1 + "/providers/Microsoft.Sql/administrators/ActiveDirectory1",),
        (server2 + "/providers/Microsoft.Sql/administrators/ActiveDirectory2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureServerADAdministrator", ["id"])
        == expected_ad_admin_nodes
    )

    # Assert - Check server-to-AD admin relationships
    expected_ad_admin_rels = {
        (server1, server1 + "/providers/Microsoft.Sql/administrators/ActiveDirectory1"),
        (server2, server2 + "/providers/Microsoft.Sql/administrators/ActiveDirectory2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureServerADAdministrator",
            "id",
            "ADMINISTERED_BY",
            rel_direction_right=True,
        )
        == expected_ad_admin_rels
    )

    # Assert - Check recoverable databases exist
    expected_recoverable_db_nodes = {
        (server1 + "/recoverabledatabases/RD1",),
        (server2 + "/recoverabledatabases/RD2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureRecoverableDatabase", ["id"])
        == expected_recoverable_db_nodes
    )

    # Assert - Check server-to-recoverable database relationships
    expected_recoverable_db_rels = {
        (server1, server1 + "/recoverabledatabases/RD1"),
        (server2, server2 + "/recoverabledatabases/RD2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureRecoverableDatabase",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_recoverable_db_rels
    )

    # Assert - Check restorable dropped databases exist
    expected_restorable_dropped_db_nodes = {
        (server1 + "/restorableDroppedDatabases/RDD1,001",),
        (server2 + "/restorableDroppedDatabases/RDD2,002",),
    }
    assert (
        check_nodes(neo4j_session, "AzureRestorableDroppedDatabase", ["id"])
        == expected_restorable_dropped_db_nodes
    )

    # Assert - Check server-to-restorable dropped database relationships
    expected_restorable_dropped_db_rels = {
        (server1, server1 + "/restorableDroppedDatabases/RDD1,001"),
        (server2, server2 + "/restorableDroppedDatabases/RDD2,002"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureRestorableDroppedDatabase",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_restorable_dropped_db_rels
    )

    # Assert - Check failover groups exist
    expected_failover_group_nodes = {
        (server1 + "/failoverGroups/FG1",),
        (server2 + "/failoverGroups/FG1",),
    }
    assert (
        check_nodes(neo4j_session, "AzureFailoverGroup", ["id"])
        == expected_failover_group_nodes
    )

    # Assert - Check server-to-failover group relationships
    expected_failover_group_rels = {
        (server1, server1 + "/failoverGroups/FG1"),
        (server2, server2 + "/failoverGroups/FG1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureFailoverGroup",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_failover_group_rels
    )

    # Assert - Check elastic pools exist
    expected_elastic_pool_nodes = {
        (server1 + "/elasticPools/EP1",),
        (server2 + "/elasticPools/EP2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureElasticPool", ["id"])
        == expected_elastic_pool_nodes
    )

    # Assert - Check server-to-elastic pool relationships
    expected_elastic_pool_rels = {
        (server1, server1 + "/elasticPools/EP1"),
        (server2, server2 + "/elasticPools/EP2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLServer",
            "id",
            "AzureElasticPool",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_elastic_pool_rels
    )

    # Assert - Check replication links exist
    expected_replication_link_nodes = {
        (server1 + "/databases/testdb1/replicationLinks/RL1",),
        (server2 + "/databases/testdb2/replicationLinks/RL2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureReplicationLink", ["id"])
        == expected_replication_link_nodes
    )

    # Assert - Check database-to-replication link relationships
    expected_replication_link_rels = {
        (
            server1 + "/databases/testdb1",
            server1 + "/databases/testdb1/replicationLinks/RL1",
        ),
        (
            server2 + "/databases/testdb2",
            server2 + "/databases/testdb2/replicationLinks/RL2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLDatabase",
            "id",
            "AzureReplicationLink",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_replication_link_rels
    )

    # Assert - Check threat detection policies exist
    expected_threat_detection_nodes = {
        (server1 + "/databases/testdb1/securityAlertPolicies/TDP1",),
        (server2 + "/databases/testdb2/securityAlertPolicies/TDP2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureDatabaseThreatDetectionPolicy", ["id"])
        == expected_threat_detection_nodes
    )

    # Assert - Check database-to-threat detection policy relationships
    expected_threat_detection_rels = {
        (
            server1 + "/databases/testdb1",
            server1 + "/databases/testdb1/securityAlertPolicies/TDP1",
        ),
        (
            server2 + "/databases/testdb2",
            server2 + "/databases/testdb2/securityAlertPolicies/TDP2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLDatabase",
            "id",
            "AzureDatabaseThreatDetectionPolicy",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_threat_detection_rels
    )

    # Assert - Check restore points exist
    expected_restore_point_nodes = {
        (server1 + "/databases/testdb1/restorepoints/RP1",),
        (server2 + "/databases/testdb2/restorepoints/RP2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureRestorePoint", ["id"])
        == expected_restore_point_nodes
    )

    # Assert - Check database-to-restore point relationships
    expected_restore_point_rels = {
        (
            server1 + "/databases/testdb1",
            server1 + "/databases/testdb1/restorepoints/RP1",
        ),
        (
            server2 + "/databases/testdb2",
            server2 + "/databases/testdb2/restorepoints/RP2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLDatabase",
            "id",
            "AzureRestorePoint",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_restore_point_rels
    )

    # Assert - Check transparent data encryptions exist
    expected_tde_nodes = {
        (server1 + "/databases/testdb1/transparentDataEncryption/TAE1",),
        (server2 + "/databases/testdb2/transparentDataEncryption/TAE2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureTransparentDataEncryption", ["id"])
        == expected_tde_nodes
    )

    # Assert - Check database-to-transparent data encryption relationships
    expected_tde_rels = {
        (
            server1 + "/databases/testdb1",
            server1 + "/databases/testdb1/transparentDataEncryption/TAE1",
        ),
        (
            server2 + "/databases/testdb2",
            server2 + "/databases/testdb2/transparentDataEncryption/TAE2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSQLDatabase",
            "id",
            "AzureTransparentDataEncryption",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_tde_rels
    )
