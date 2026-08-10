from cartography.intel.azure.sql import transform_sql_database
from cartography.intel.azure.sql import transform_sql_detail
from cartography.intel.azure.sql import transform_sql_firewall_rule
from cartography.intel.azure.sql import transform_sql_server


def test_transform_sql_server_flattens_sdk_4_properties():
    server = transform_sql_server(
        {
            "id": "server-id",
            "name": "server",
            "properties": {
                "publicNetworkAccess": "Enabled",
                "minimalTlsVersion": "1.2",
            },
        }
    )

    assert server["public_network_access"] == "Enabled"
    assert server["minimal_tls_version"] == "1.2"


def test_transform_sql_firewall_rule_flattens_sdk_4_properties():
    rule = transform_sql_firewall_rule(
        {
            "id": "rule-id",
            "name": "AllowAll",
            "properties": {
                "startIpAddress": "0.0.0.0",
                "endIpAddress": "255.255.255.255",
            },
        }
    )

    assert rule["start_ip_address"] == "0.0.0.0"
    assert rule["end_ip_address"] == "255.255.255.255"


def test_transform_sql_database_flattens_sdk_4_properties():
    database = transform_sql_database(
        {
            "id": "database-id",
            "name": "database",
            "properties": {
                "creationDate": "2026-07-01T00:00:00Z",
                "databaseId": "database-guid",
                "maxSizeBytes": 1024,
                "licenseType": "LicenseIncluded",
                "defaultSecondaryLocation": "westus",
                "elasticPoolId": "pool-id",
                "failoverGroupId": "failover-id",
                "zoneRedundant": True,
            },
        }
    )

    assert database["creation_date"] == "2026-07-01T00:00:00Z"
    assert database["database_id"] == "database-guid"
    assert database["max_size_bytes"] == 1024
    assert database["license_type"] == "LicenseIncluded"
    assert database["default_secondary_location"] == "westus"
    assert database["elastic_pool_id"] == "pool-id"
    assert database["failover_group_id"] == "failover-id"
    assert database["zone_redundant"] is True


def test_transform_sql_detail_flattens_common_sdk_4_properties():
    detail = transform_sql_detail(
        {
            "id": "detail-id",
            "name": "detail",
            "properties": {
                "azureDnsRecord": "server.database.windows.net",
                "administratorType": "ActiveDirectory",
                "replicationState": "CATCH_UP",
                "emailAccountAdmins": True,
                "restorePointCreationDate": "2026-07-01T00:00:00Z",
                "status": "Enabled",
            },
        }
    )

    assert detail["azure_dns_record"] == "server.database.windows.net"
    assert detail["administrator_type"] == "ActiveDirectory"
    assert detail["replication_state"] == "CATCH_UP"
    assert detail["email_account_admins"] is True
    assert detail["restore_point_creation_date"] == "2026-07-01T00:00:00Z"
    assert detail["status"] == "Enabled"
