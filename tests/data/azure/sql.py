DESCRIBE_SERVERS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        "name": "testSQL1",
        "type": "Microsoft.Sql/servers",
        "location": "Central India",
        "kind": "v12.0",
        "version": "12.0",
        "state": "Ready",
        "resourceGroup": "TestRG",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        "name": "testSQL2",
        "type": "Microsoft.Sql/servers",
        "location": "Central India",
        "kind": "v12.0",
        "version": "12.0",
        "state": "Ready",
        "resourceGroup": "TestRG",
    },
]

server1 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1"
server2 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2"

DESCRIBE_DNS_ALIASES = [
    {
        "id": server1 + "/dnsAliases/dns-alias-1",
        "name": "server-dns-alias-1",
        "type": "Microsoft.Sql/servers/dnsAliases",
        "azure_dns_record": "dns-alias-1.database.windows.net",
        "server_id": server1,
    },
    {
        "id": server2 + "/dnsAliases/dns-alias-2",
        "name": "server-dns-alias-2",
        "type": "Microsoft.Sql/servers/dnsAliases",
        "azure_dns_record": "dns-alias-2.database.windows.net",
        "server_id": server2,
    },
]


DESCRIBE_AD_ADMINS = [
    {
        "id": server1 + "/providers/Microsoft.Sql/administrators/ActiveDirectory1",
        "name": "ActiveDirectory1",
        "administrator_type": "ActiveDirectory",
        "login": "DSEngAll",
        "server_id": server1,
    },
    {
        "id": server2 + "/providers/Microsoft.Sql/administrators/ActiveDirectory2",
        "name": "ActiveDirectory2",
        "administrator_type": "ActiveDirectory",
        "login": "DSEngAll",
        "server_id": server2,
    },
]


DESCRIBE_RECOVERABLE_DATABASES = [
    {
        "id": server1 + "/recoverabledatabases/RD1",
        "name": "RD1",
        "type": "Microsoft.Sql/servers/recoverabledatabases",
        "edition": "Standard",
        "service_level_objective": "S0",
        "last_available_backup_date": "2020-05-26T01:06:29.78Z",
        "server_id": server1,
    },
    {
        "id": server2 + "/recoverabledatabases/RD2",
        "name": "RD2",
        "type": "Microsoft.Sql/servers/recoverabledatabases",
        "edition": "Premium",
        "service_level_objective": "P1",
        "last_available_backup_date": "2020-05-26T03:20:31.78Z",
        "server_id": server2,
    },
]


DESCRIBE_RESTORABLE_DROPPED_DATABASES = [
    {
        "id": server1 + "/restorableDroppedDatabases/RDD1,001",
        "name": "RDD1,001",
        "type": "Microsoft.Sql/servers/restorableDroppedDatabases",
        "location": "Central India",
        "database_name": "RDD1",
        "edition": "Basic",
        "max_size_bytes": "2147483648",
        "service_level_objective": "Basic",
        "creation_date": "2020-02-10T00:56:19.2Z",
        "deletion_date": "2020-05-27T02:49:47.69Z",
        "earliest_restore_date": "2020-05-20T02:49:47.69Z",
        "server_id": server1,
    },
    {
        "id": server2 + "/restorableDroppedDatabases/RDD2,002",
        "name": "RDD2,002",
        "type": "Microsoft.Sql/servers/restorableDroppedDatabases",
        "location": "Central India",
        "database_name": "RDD2",
        "edition": "Standard",
        "max_size_bytes": "268435456000",
        "service_level_objective": "S0",
        "creation_date": "2020-05-10T00:56:19.2Z",
        "earliest_restore_date": "2020-04-21T02:49:47.69Z",
        "server_id": server2,
    },
]


DESCRIBE_FAILOVER_GROUPS = [
    {
        "id": server1 + "/failoverGroups/FG1",
        "name": "FG1",
        "type": "Microsoft.Sql/servers/failoverGroups",
        "location": "Central India",
        "replication_role": "Primary",
        "replication_state": "CATCH_UP",
        "partner_servers": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
                "location": "Central India",
                "replication_role": "Secondary",
            },
        ],
        "server_id": server1,
    },
    {
        "id": server2 + "/failoverGroups/FG1",
        "name": "FG1",
        "type": "Microsoft.Sql/servers/failoverGroups",
        "location": "Central India",
        "replication_role": "Secondary",
        "replication_state": "CATCH_UP",
        "partner_servers": [
            {
                "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
                "location": "Central India",
                "replication_role": "Primary",
            },
        ],
        "server_id": server2,
    },
]


DESCRIBE_ELASTIC_POOLS = [
    {
        "id": server1 + "/elasticPools/EP1",
        "name": "EP1",
        "type": "Microsoft.Sql/servers/elasticPools",
        "location": "Central India",
        "creation_date": "2017-02-10T01:27:21.32Z",
        "state": "Ready",
        "max_size_bytes": 5242880000,
        "zone_redundant": True,
        "license_type": "LicenseIncluded",
        "server_id": server1,
    },
    {
        "id": server2 + "/elasticPools/EP2",
        "name": "EP2",
        "type": "Microsoft.Sql/servers/elasticPools",
        "location": "Central India",
        "creation_date": "2017-02-10T01:27:21.32Z",
        "state": "Ready",
        "max_size_bytes": 5242880000,
        "zone_redundant": True,
        "license_type": "LicenseIncluded",
        "server_id": server2,
    },
]


DESCRIBE_DATABASES = [
    {
        "kind": "v12.0,user,vcore",
        "collation": "SQL_Latin1_General_CP1_CI_AS",
        "max_size_bytes": 268435456000,
        "status": "Online",
        "database_id": "6c764297-577b-470f-9af4-96d3d41e2ba3",
        "creation_date": "2017-06-07T04:41:33.937Z",
        "default_secondary_location": "North Europe",
        "license_type": "LicenseIncluded",
        "zone_redundant": False,
        "location": "Central India",
        "id": server1 + "/databases/testdb1",
        "name": "testdb1",
        "type": "Microsoft.Sql/servers/databases",
        "server_id": server1,
    },
    {
        "kind": "v12.0,user,vcore",
        "collation": "SQL_Latin1_General_CP1_CI_AS",
        "max_size_bytes": 268435456000,
        "status": "Online",
        "database_id": "6c764297-577b-470f-9af4-96d3d41e2ba3",
        "creation_date": "2017-06-07T04:41:33.937Z",
        "default_secondary_location": "Central India",
        "license_type": "LicenseIncluded",
        "zone_redundant": False,
        "location": "North Europe",
        "id": server2 + "/databases/testdb2",
        "name": "testdb2",
        "type": "Microsoft.Sql/servers/databases",
        "server_id": server2,
    },
]


DESCRIBE_REPLICATION_LINKS = [
    {
        "id": server1 + "/databases/testdb1/replicationLinks/RL1",
        "name": "RL1",
        "type": "Microsoft.Sql/servers/databases/replicationLinks",
        "location": "North Europe",
        "partner_server": "testSQL2",
        "partner_database": "testdb2",
        "partner_location": "North Europe",
        "role": "Secondary",
        "partner_role": "Primary",
        "replication_mode": "ASYNC",
        "start_time": "2017-02-10T01:44:27.117Z",
        "percent_complete": 100,
        "replication_state": "CATCH_UP",
        "is_termination_allowed": True,
        "database_id": server1 + "/databases/testdb1",
    },
    {
        "id": server2 + "/databases/testdb2/replicationLinks/RL2",
        "name": "RL2",
        "type": "Microsoft.Sql/servers/databases/replicationLinks",
        "location": "North Europe",
        "partner_server": "testSQL1",
        "partner_database": "testdb1",
        "partner_location": "Central India",
        "role": "Primary",
        "partner_role": "Secondary",
        "replication_mode": "ASYNC",
        "start_time": "2017-02-10T01:44:27.117Z",
        "percent_complete": 100,
        "replication_state": "CATCH_UP",
        "is_termination_allowed": True,
        "database_id": server2 + "/databases/testdb2",
    },
]


DESCRIBE_THREAT_DETECTION_POLICY = [
    {
        "id": server1 + "/databases/testdb1/securityAlertPolicies/TDP1",
        "name": "TDP1",
        "type": "Microsoft.Sql/servers/databases/securityAlertPolicies",
        "location": "Central India",
        "kind": "V12",
        "state": "Enabled",
        "email_account_admins": "Enabled",
        "email_addresses": "test@microsoft.com;user@microsoft.com",
        "disabled_alerts": "Usage_Anomaly",
        "retention_days": 0,
        "storageAccountAccessKey": "",
        "storage_endpoint": "",
        "use_server_default": "Enabled",
        "database_id": server1 + "/databases/testdb1",
    },
    {
        "id": server2 + "/databases/testdb2/securityAlertPolicies/TDP2",
        "name": "TDP2",
        "type": "Microsoft.Sql/servers/databases/securityAlertPolicies",
        "location": "Central India",
        "kind": "V12",
        "state": "Enabled",
        "email_account_admins": "Enabled",
        "email_addresses": "test@microsoft.com;user@microsoft.com",
        "disabled_alerts": "Usage_Anomaly",
        "retention_days": 0,
        "storageAccountAccessKey": "",
        "storage_endpoint": "",
        "use_server_default": "Enabled",
        "database_id": server2 + "/databases/testdb2",
    },
]


DESCRIBE_RESTORE_POINTS = [
    {
        "id": server1 + "/databases/testdb1/restorepoints/RP1",
        "name": "RP1",
        "location": "Central India",
        "type": "Microsoft.Sql/servers/databases/restorePoints",
        "restore_point_type": "DISCRETE",
        "restore_point_creation_date": "2017-07-18T03:09:27Z",
        "database_id": server1 + "/databases/testdb1",
    },
    {
        "id": server2 + "/databases/testdb2/restorepoints/RP2",
        "name": "RP2",
        "location": "Central India",
        "type": "Microsoft.Sql/servers/databases/restorePoints",
        "restore_point_type": "DISCRETE",
        "restore_point_creation_date": "2017-07-18T03:09:27Z",
        "database_id": server2 + "/databases/testdb2",
    },
]


DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS = [
    {
        "name": "TAE1",
        "location": "Central India",
        "id": server1 + "/databases/testdb1/transparentDataEncryption/TAE1",
        "type": "Microsoft.Sql/servers/databases/transparentDataEncryption",
        "status": "Enabled",
        "database_id": server1 + "/databases/testdb1",
    },
    {
        "name": "TAE2",
        "location": "Central India",
        "id": server2 + "/databases/testdb2/transparentDataEncryption/TAE2",
        "type": "Microsoft.Sql/servers/databases/transparentDataEncryption",
        "status": "Enabled",
        "database_id": server2 + "/databases/testdb2",
    },
]
