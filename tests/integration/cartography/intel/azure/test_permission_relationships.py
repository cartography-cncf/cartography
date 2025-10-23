from typing import Any
from typing import AsyncGenerator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import yaml

import cartography.intel.azure.compute
import cartography.intel.azure.cosmosdb
import cartography.intel.azure.rbac
import cartography.intel.azure.sql
import cartography.intel.azure.storage
import cartography.intel.azure.subscription
import cartography.intel.azure.tenant
import cartography.intel.entra.groups
import cartography.intel.entra.service_principals
import cartography.intel.entra.users
from cartography.intel.azure import permission_relationships
from tests.data.azure.permission_relationships import AZURE_COSMOSDB_ACCOUNTS
from tests.data.azure.permission_relationships import AZURE_SQL_SERVERS
from tests.data.azure.permission_relationships import AZURE_STORAGE_ACCOUNTS
from tests.data.azure.permission_relationships import AZURE_VMS
from tests.data.azure.permission_relationships import PERMISSION_RELATIONSHIPS_YAML
from tests.data.azure.rbac import AZURE_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_ROLE_DEFINITIONS
from tests.data.azure.rbac import ENTRA_GROUPS
from tests.data.azure.rbac import ENTRA_SERVICE_PRINCIPALS
from tests.data.azure.rbac import ENTRA_USERS
from tests.data.azure.rbac import MOCK_ENTRA_TENANT
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.cartography.intel.entra.common import create_test_entra_tenant
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789012"
TEST_TENANT_ID = "tenant-123"
TEST_UPDATE_TAG = 123456789


async def async_generator_from_list(items: list[Any]) -> AsyncGenerator[Any, None]:
    """Helper function to create an async generator from a list for mocking purposes."""
    for item in items:
        yield item


async def async_return_empty_list():
    """Helper function to return an empty list asynchronously."""
    return []


async def async_return_empty_tuple():
    """Helper function to return an empty tuple asynchronously."""
    return ([], [])


@patch.object(
    cartography.intel.entra.service_principals,
    "get_entra_service_principals",
    return_value=async_generator_from_list(ENTRA_SERVICE_PRINCIPALS),
)
@patch.object(
    cartography.intel.entra.groups,
    "get_group_owners",
    return_value=async_return_empty_list(),
)
@patch.object(
    cartography.intel.entra.groups,
    "get_group_members",
    return_value=async_return_empty_tuple(),
)
@patch.object(
    cartography.intel.entra.groups,
    "get_entra_groups",
    return_value=async_generator_from_list(ENTRA_GROUPS),
)
@patch.object(
    cartography.intel.entra.users,
    "get_tenant",
    return_value=MOCK_ENTRA_TENANT,
)
@patch.object(
    cartography.intel.entra.users,
    "get_users",
    return_value=async_generator_from_list(ENTRA_USERS),
)
@patch.object(
    cartography.intel.azure.storage,
    "get_storage_account_list",
    return_value=AZURE_STORAGE_ACCOUNTS,
)
@patch.object(
    cartography.intel.azure.storage,
    "get_queue_services",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_table_services",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_file_services",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_blob_services",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_queue_services_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_table_services_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_file_services_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_blob_services_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.compute,
    "get_snapshots_list",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.compute,
    "get_disks",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.compute,
    "get_vm_list",
    return_value=AZURE_VMS,
)
@patch.object(
    cartography.intel.azure.sql,
    "get_server_list",
    return_value=AZURE_SQL_SERVERS,
)
@patch.object(
    cartography.intel.azure.sql,
    "get_server_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_dns_aliases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_ad_admins",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_recoverable_databases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_restorable_dropped_databases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_failover_groups",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_elastic_pools",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_databases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_database_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_replication_links",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_db_threat_detection_policies",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_restore_points",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.sql,
    "get_transparent_data_encryptions",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_database_account_list",
    return_value=AZURE_COSMOSDB_ACCOUNTS,
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_database_account_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_sql_databases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_cassandra_keyspaces",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_mongodb_databases",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_table_resources",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_sql_database_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_sql_containers",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_cassandra_keyspace_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_cassandra_tables",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_mongodb_databases_details",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_mongodb_collections",
    return_value=[],
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments",
    return_value=AZURE_ROLE_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_ROLE_DEFINITIONS,
)
@patch.object(
    permission_relationships,
    "parse_permission_relationships_file",
    return_value=yaml.load(PERMISSION_RELATIONSHIPS_YAML, Loader=yaml.FullLoader),
)
@pytest.mark.asyncio
async def test_sync_azure_permission_relationships(
    mock_get_users,
    mock_get_tenant,
    mock_get_entra_groups,
    mock_get_group_members,
    mock_get_group_owners,
    mock_get_role_definitions,
    mock_get_role_assignments,
    mock_get_sql_servers,
    mock_get_server_details,
    mock_get_dns_aliases,
    mock_get_ad_admins,
    mock_get_recoverable_databases,
    mock_get_restorable_dropped_databases,
    mock_get_failover_groups,
    mock_get_elastic_pools,
    mock_get_databases,
    mock_get_database_details,
    mock_get_replication_links,
    mock_get_db_threat_detection_policies,
    mock_get_restore_points,
    mock_get_transparent_data_encryptions,
    mock_get_cosmosdb,
    mock_get_database_account_details,
    mock_get_sql_databases,
    mock_get_cassandra_keyspaces,
    mock_get_mongodb_databases,
    mock_get_table_resources,
    mock_get_sql_database_details,
    mock_get_sql_containers,
    mock_get_cassandra_keyspace_details,
    mock_get_cassandra_tables,
    mock_get_mongodb_databases_details,
    mock_get_mongodb_collections,
    mock_get_vms,
    mock_get_disks,
    mock_get_snapshots_list,
    mock_get_storage,
    mock_get_queue_services,
    mock_get_table_services,
    mock_get_file_services,
    mock_get_blob_services,
    mock_get_queue_services_details,
    mock_get_table_services_details,
    mock_get_file_services_details,
    mock_get_blob_services_details,
    mock_get_entra_service_principals,
    mock_parse_permission_relationships_file,
    neo4j_session,
):

    # Arrange

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        "AZURE_ID": TEST_SUBSCRIPTION_ID,
        "azure_permission_relationships_file": "dummy_path",  # Will be mocked
    }

    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    create_test_entra_tenant(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG)
    mock_credentials = MagicMock()

    # Act
    await cartography.intel.entra.users.sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    await cartography.intel.entra.groups.sync_entra_groups(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    await cartography.intel.entra.service_principals.sync_service_principals(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cartography.intel.azure.sql.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cartography.intel.azure.storage.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cartography.intel.azure.compute.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cartography.intel.azure.cosmosdb.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cartography.intel.azure.rbac.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    permission_relationships.sync(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert

    # Alice (user-123) has Owner role, so should have CAN_MANAGE, CAN_READ, CAN_WRITE on SQL servers
    # Bob (user-456) has Reader role, so should have CAN_READ on SQL servers
    # SQL Admins group (group-789) has SQL Server Contributor role, so should have CAN_MANAGE, CAN_READ, CAN_WRITE on SQL servers
    # Test App (app-101) has Reader role, so should have CAN_READ on SQL servers

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_MANAGE",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_WRITE",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraGroup",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_MANAGE",
        rel_direction_right=True,
    ) == {
        (
            "group-789",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "group-789",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraServicePrincipal",
        "id",
        "AzureSQLServer",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "sp-101",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            "sp-101",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureStorageAccount",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/teststorage1",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/teststorage1",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureVirtualMachine",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/testVM1",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/testVM1",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "AzureCosmosDBAccount",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        (
            "user-123",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.DocumentDB/databaseAccounts/testcosmos1",
        ),
        (
            "user-456",
            "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.DocumentDB/databaseAccounts/testcosmos1",
        ),
    }
