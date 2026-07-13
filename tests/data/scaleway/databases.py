from datetime import datetime

from dateutil.tz import tzutc
from scaleway.datawarehouse.v1beta1 import Deployment as DWDeployment
from scaleway.mongodb.v1 import Endpoint as MongoEndpoint
from scaleway.mongodb.v1 import EndpointPrivateNetworkDetails as MongoPrivateNetDetails
from scaleway.mongodb.v1 import EndpointPublicNetworkDetails as MongoPublicNetDetails
from scaleway.mongodb.v1 import Instance as MongoInstance
from scaleway.mongodb.v1 import Volume as MongoVolume
from scaleway.mongodb.v1 import VolumeType as MongoVolumeType
from scaleway.rdb.v1 import BackupSchedule as RdbBackupSchedule
from scaleway.rdb.v1 import EncryptionAtRest as RdbEncryptionAtRest
from scaleway.rdb.v1 import Endpoint as RdbEndpoint
from scaleway.rdb.v1 import EndpointLoadBalancerDetails as RdbLBDetails
from scaleway.rdb.v1 import EndpointPrivateNetworkDetails as RdbPrivateNetDetails
from scaleway.rdb.v1 import Instance as RdbInstance
from scaleway.rdb.v1 import Volume as RdbVolume
from scaleway.rdb.v1 import VolumeType as RdbVolumeType
from scaleway.redis.v1 import Cluster as RedisCluster
from scaleway.redis.v1 import Endpoint as RedisEndpoint
from scaleway.redis.v1 import PrivateNetwork as RedisPrivateNet
from scaleway.redis.v1 import PublicNetwork as RedisPublicNet
from scaleway.searchdb.v1alpha1 import Deployment as SearchDeployment
from scaleway.serverless_sqldb.v1alpha1 import Database as ServerlessSqlDatabase

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
# Reuse the network-test ID so the ATTACHED_TO edge resolves against the
# private network loaded by tests/data/scaleway/network.py.
TEST_PRIVATE_NETWORK_ID = "22222222-2222-4820-b8d6-0eef10cfcd6d"

TEST_RDB_INSTANCE_ID = "aaaa1111-1111-4820-b8d6-0eef10cfcd6d"
TEST_REDIS_CLUSTER_ID = "bbbb2222-2222-4820-b8d6-0eef10cfcd6d"
TEST_MONGO_INSTANCE_ID = "cccc3333-3333-4820-b8d6-0eef10cfcd6d"


SCALEWAY_RDB_INSTANCES = [
    RdbInstance(
        id=TEST_RDB_INSTANCE_ID,
        name="demo-rdb",
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        status="ready",
        engine="PostgreSQL-15",
        tags=["demo"],
        settings=[],
        upgradable_version=[],
        is_ha_cluster=False,
        read_replicas=[],
        node_type="DB-DEV-S",
        init_settings=[],
        endpoints=[
            RdbEndpoint(
                id="ep-lb-1",
                port=5432,
                name=None,
                ip="51.159.0.50",
                hostname="demo-rdb.scw.cloud",
                private_network=None,
                load_balancer=RdbLBDetails(),
                direct_access=None,
            ),
            RdbEndpoint(
                id="ep-pn-1",
                port=5432,
                name=None,
                ip="172.16.16.10",
                hostname=None,
                private_network=RdbPrivateNetDetails(
                    private_network_id=TEST_PRIVATE_NETWORK_ID,
                    service_ip="172.16.16.10/22",
                    zone="fr-par-1",
                    provisioning_mode="ipam",
                ),
                load_balancer=None,
                direct_access=None,
            ),
        ],
        backup_same_region=True,
        maintenances=[],
        region="fr-par",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        volume=RdbVolume(
            type_=RdbVolumeType.SBS_5K,
            size=10737418240,
            class_="sbs",
        ),
        endpoint=None,
        backup_schedule=RdbBackupSchedule(
            frequency=24,
            retention=604800,
            disabled=False,
            next_run_at=datetime(2025, 3, 21, 0, 0, 0, tzinfo=tzutc()),
        ),
        logs_policy=None,
        encryption=RdbEncryptionAtRest(enabled=True),
    ),
]


SCALEWAY_REDIS_CLUSTERS = [
    RedisCluster(
        id=TEST_REDIS_CLUSTER_ID,
        name="demo-redis",
        project_id=TEST_PROJECT_ID,
        status="ready",
        version="7.0.5",
        endpoints=[
            RedisEndpoint(
                port=6379,
                ips=["51.159.0.60"],
                id="redis-ep-public",
                private_network=None,
                public_network=RedisPublicNet(),
            ),
            RedisEndpoint(
                port=6379,
                ips=["172.16.16.20"],
                id="redis-ep-private",
                private_network=RedisPrivateNet(
                    id=TEST_PRIVATE_NETWORK_ID,
                    service_ips=["172.16.16.20/22"],
                    zone="fr-par-1",
                    provisioning_mode="ipam",
                ),
                public_network=None,
            ),
        ],
        tags=["demo"],
        node_type="RED1-MICRO",
        tls_enabled=True,
        cluster_settings=[],
        acl_rules=[],
        cluster_size=1,
        zone="fr-par-1",
        user_name="default",
        upgradable_versions=[],
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    ),
]


SCALEWAY_MONGO_INSTANCES = [
    MongoInstance(
        id=TEST_MONGO_INSTANCE_ID,
        name="demo-mongo",
        project_id=TEST_PROJECT_ID,
        organization_id=TEST_ORG_ID,
        status="ready",
        version="7.0",
        tags=["demo"],
        node_amount=1,
        node_type="MGDB-PLAY2-NANO",
        endpoints=[
            MongoEndpoint(
                id="mongo-ep-public",
                dns_record="demo-mongo.public.mgdb.scw.cloud",
                port=27017,
                private_network=None,
                public_network=MongoPublicNetDetails(),
            ),
            MongoEndpoint(
                id="mongo-ep-private",
                dns_record="demo-mongo.private.mgdb.scw.cloud",
                port=27017,
                private_network=MongoPrivateNetDetails(
                    private_network_id=TEST_PRIVATE_NETWORK_ID,
                ),
                public_network=None,
            ),
        ],
        region="fr-par",
        settings=[],
        volume=MongoVolume(type_=MongoVolumeType.SBS_5K, size_bytes=5368709120),
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        snapshot_schedule=None,
    ),
]

SCALEWAY_DATAWAREHOUSE = [
    DWDeployment(
        id="dw000000-0000-0000-0000-000000000001",
        name="analytics-dw",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        status="ready",
        tags=["demo"],
        version="24.8",
        replica_count=2,
        shard_count=1,
        cpu_min=2,
        cpu_max=8,
        endpoints=[],
        ram_per_cpu=4,
        region="fr-par",
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]

SCALEWAY_SERVERLESS_SQL = [
    ServerlessSqlDatabase(
        id="sq000000-0000-0000-0000-000000000001",
        name="serverless-pg",
        status="ready",
        endpoint="postgres://serverless-pg.fr-par.sdb.scw.cloud:5432/main",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        region="fr-par",
        cpu_min=0,
        cpu_max=8,
        cpu_current=1,
        started=True,
        engine_major_version="16",
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]

SCALEWAY_SEARCHDB = [
    SearchDeployment(
        id="se000000-0000-0000-0000-000000000001",
        name="logs-search",
        organization_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        project_id="0681c477-fbb9-4820-b8d6-0eef10cfcd6d",
        status="ready",
        tags=["demo"],
        node_amount=3,
        node_type="essentials",
        endpoints=[],
        version="2.17",
        region="fr-par",
        created_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 10, 58, 0, 784077, tzinfo=tzutc()),
    ),
]
