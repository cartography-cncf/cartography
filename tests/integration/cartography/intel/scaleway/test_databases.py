from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.databases.mongodb
import cartography.intel.scaleway.databases.rdb
import cartography.intel.scaleway.databases.redis
import cartography.intel.scaleway.network.private_networks
from tests.data.scaleway.databases import SCALEWAY_MONGO_INSTANCES
from tests.data.scaleway.databases import SCALEWAY_RDB_INSTANCES
from tests.data.scaleway.databases import SCALEWAY_REDIS_CLUSTERS
from tests.data.scaleway.databases import TEST_MONGO_INSTANCE_ID
from tests.data.scaleway.databases import TEST_PRIVATE_NETWORK_ID
from tests.data.scaleway.databases import TEST_RDB_INSTANCE_ID
from tests.data.scaleway.databases import TEST_REDIS_CLUSTER_ID
from tests.data.scaleway.network import SCALEWAY_PRIVATE_NETWORKS
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.databases.mongodb,
    "get",
    return_value=SCALEWAY_MONGO_INSTANCES,
)
@patch.object(
    cartography.intel.scaleway.databases.redis,
    "get",
    return_value=SCALEWAY_REDIS_CLUSTERS,
)
@patch.object(
    cartography.intel.scaleway.databases.rdb,
    "get",
    return_value=SCALEWAY_RDB_INSTANCES,
)
@patch.object(
    cartography.intel.scaleway.network.private_networks,
    "get",
    return_value=SCALEWAY_PRIVATE_NETWORKS,
)
def test_load_scaleway_databases(
    _mock_pn_get,
    _mock_rdb_get,
    _mock_redis_get,
    _mock_mongo_get,
    neo4j_session,
):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act: load private networks first so ATTACHED_TO edges resolve.
    cartography.intel.scaleway.network.private_networks.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.scaleway.databases.rdb.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.scaleway.databases.redis.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.scaleway.databases.mongodb.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewayRdbInstance", ["id", "name"]) == {
        (TEST_RDB_INSTANCE_ID, "demo-rdb"),
    }
    assert check_nodes(neo4j_session, "ScalewayRedisCluster", ["id", "name"]) == {
        (TEST_REDIS_CLUSTER_ID, "demo-redis"),
    }
    assert check_nodes(neo4j_session, "ScalewayMongoDBInstance", ["id", "name"]) == {
        (TEST_MONGO_INSTANCE_ID, "demo-mongo"),
    }

    # Assert flattened endpoint fields
    assert check_nodes(
        neo4j_session,
        "ScalewayRdbInstance",
        [
            "id",
            "is_public",
            "public_endpoint_ip",
            "public_endpoint_port",
            "private_endpoint_ip",
            "encryption_at_rest_enabled",
            "backup_schedule_retention_days",
            "volume_size",
        ],
    ) == {
        (
            TEST_RDB_INSTANCE_ID,
            True,
            "51.159.0.50",
            5432,
            "172.16.16.10",
            True,
            7,
            10737418240,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "ScalewayRedisCluster",
        [
            "id",
            "is_public",
            "public_endpoint_ip",
            "private_endpoint_ip",
            "tls_enabled",
        ],
    ) == {
        (TEST_REDIS_CLUSTER_ID, True, "51.159.0.60", "172.16.16.20", True),
    }
    assert check_nodes(
        neo4j_session,
        "ScalewayMongoDBInstance",
        [
            "id",
            "is_public",
            "public_endpoint_dns",
            "private_endpoint_dns",
            "node_amount",
            "volume_size",
        ],
    ) == {
        (
            TEST_MONGO_INSTANCE_ID,
            True,
            "demo-mongo.public.mgdb.scw.cloud",
            "demo-mongo.private.mgdb.scw.cloud",
            1,
            5368709120,
        ),
    }

    # Cross-cloud ontology label
    assert check_nodes(neo4j_session, "Database", ["id"]) >= {
        (TEST_RDB_INSTANCE_ID,),
        (TEST_REDIS_CLUSTER_ID,),
        (TEST_MONGO_INSTANCE_ID,),
    }

    # Project ownership
    for label in (
        "ScalewayRdbInstance",
        "ScalewayRedisCluster",
        "ScalewayMongoDBInstance",
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Attached private network
    for label, db_id in (
        ("ScalewayRdbInstance", TEST_RDB_INSTANCE_ID),
        ("ScalewayRedisCluster", TEST_REDIS_CLUSTER_ID),
        ("ScalewayMongoDBInstance", TEST_MONGO_INSTANCE_ID),
    ):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayPrivateNetwork",
            "id",
            "ATTACHED_TO",
            rel_direction_right=True,
        ) == {
            (db_id, TEST_PRIVATE_NETWORK_ID),
        }, f"{label} not attached to private network"

    # Normalized _ont_db_* fields populated from the Database mapping.
    rdb_rows = check_nodes(
        neo4j_session,
        "Database",
        ["id", "_ont_name", "_ont_type", "_ont_encrypted", "_ont_source"],
    )
    assert (
        TEST_RDB_INSTANCE_ID,
        "demo-rdb",
        "PostgreSQL-15",
        True,
        "scaleway",
    ) in rdb_rows
    assert (
        TEST_REDIS_CLUSTER_ID,
        "demo-redis",
        "redis",
        None,
        "scaleway",
    ) in rdb_rows
    assert (
        TEST_MONGO_INSTANCE_ID,
        "demo-mongo",
        "mongodb",
        None,
        "scaleway",
    ) in rdb_rows
