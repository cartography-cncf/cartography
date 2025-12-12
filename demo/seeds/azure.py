import cartography.intel.azure.compute
import cartography.intel.azure.cosmosdb
import cartography.intel.azure.sql
import cartography.intel.azure.storage
import tests.data.azure.compute
import tests.data.azure.cosmosdb
import tests.data.azure.sql
import tests.data.azure.storage
from demo.seeds.base import Seed

SUBSCRIPTION_ID = "00-00-00-00"
RESOURCE_GROUP = "TestRG"


class AzureSeed(Seed):

    def seed(self, *args) -> None:
        # TODO: Add after datamodel migration
        # self._seed_tenant()
        self._seed_subscription()
        self._seed_compute()
        self._seed_cosmosdb()
        self._seed_sql()
        self._seed_storage()

    def _seed_subscription(self):
        self.neo4j_session.run(
            """
            MERGE (as:AzureSubscription{id: $subscription_id})
            ON CREATE SET as.firstseen = timestamp()
            SET as.lastupdated = $update_tag
            """,
            subscription_id=SUBSCRIPTION_ID,
            update_tag=self.update_tag,
        )

    def _seed_compute(self) -> None:
        # VMs
        cartography.intel.azure.compute.load_vms(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.compute.DESCRIBE_VMS,
            self.update_tag,
        )
        # VM data disk
        cartography.intel.azure.compute.load_vm_data_disks(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.compute.DESCRIBE_VM_DATA_DISKS,
            self.update_tag,
        )
        # Disks
        cartography.intel.azure.compute.load_disks(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.compute.DESCRIBE_DISKS,
            self.update_tag,
        )
        # Snapshots
        cartography.intel.azure.compute.load_snapshots(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.compute.DESCRIBE_SNAPSHOTS,
            self.update_tag,
        )

    def _seed_cosmosdb(self) -> None:
        # Database Accounts
        cartography.intel.azure.cosmosdb.load_database_account_data(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.cosmosdb.DESCRIBE_DATABASE_ACCOUNTS,
            self.update_tag,
        )
        for database_account in tests.data.azure.cosmosdb.DESCRIBE_DATABASE_ACCOUNTS:
            cartography.intel.azure.cosmosdb._load_database_account_write_locations(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_database_account_read_locations(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_database_account_associated_locations(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_cosmosdb_cors_policy(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_cosmosdb_failover_policies(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_cosmosdb_private_endpoint_connections(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
            cartography.intel.azure.cosmosdb._load_cosmosdb_virtual_network_rules(
                self.neo4j_session,
                database_account,
                SUBSCRIPTION_ID,
                self.update_tag,
            )
        # SQL
        cartography.intel.azure.cosmosdb._load_sql_databases(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_SQL_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.cosmosdb._load_sql_containers(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_SQL_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        # Cassandra
        cartography.intel.azure.cosmosdb._load_cassandra_keyspaces(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_CASSANDRA_KEYSPACES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.cosmosdb._load_cassandra_tables(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_CASSANDRA_TABLES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        # MongoDB
        cartography.intel.azure.cosmosdb._load_mongodb_databases(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_MONGODB_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.cosmosdb._load_collections(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_MONGODB_COLLECTIONS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        # Table
        cartography.intel.azure.cosmosdb._load_table_resources(
            self.neo4j_session,
            tests.data.azure.cosmosdb.DESCRIBE_TABLE_RESOURCES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )

    def _seed_sql(self) -> None:
        cartography.intel.azure.sql.load_server_data(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.sql.DESCRIBE_SERVERS,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_server_dns_aliases(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_DNS_ALIASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_server_ad_admins(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_AD_ADMINS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_recoverable_databases(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_RECOVERABLE_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_restorable_dropped_databases(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_RESTORABLE_DROPPED_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_failover_groups(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_FAILOVER_GROUPS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_elastic_pools(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_ELASTIC_POOLS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_databases(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_DATABASES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_replication_links(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_REPLICATION_LINKS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_db_threat_detection_policies(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_THREAT_DETECTION_POLICY,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_restore_points(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_RESTORE_POINTS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.sql._load_transparent_data_encryptions(
            self.neo4j_session,
            tests.data.azure.sql.DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )

    def _seed_storage(self) -> None:
        cartography.intel.azure.storage.load_storage_account_data(
            self.neo4j_session,
            SUBSCRIPTION_ID,
            tests.data.azure.storage.DESCRIBE_STORAGE_ACCOUNTS,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_queue_services(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_QUEUE_SERVICES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_queues(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_QUEUE,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_table_services(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_TABLE_SERVICES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_tables(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_TABLES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_file_services(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_FILE_SERVICES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_shares(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_FILE_SHARES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_blob_services(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_BLOB_SERVICES,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
        cartography.intel.azure.storage._load_blob_containers(
            self.neo4j_session,
            tests.data.azure.storage.DESCRIBE_BLOB_CONTAINERS,
            SUBSCRIPTION_ID,
            self.update_tag,
        )
