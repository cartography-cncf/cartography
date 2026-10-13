from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.elasticache
import tests.data.aws.elasticache
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.elasticache,
    "get_elasticache_clusters",
    return_value=tests.data.aws.elasticache.DESCRIBE_CACHE_CLUSTERS["CacheClusters"],
)
def test_sync_elasticache(mock_get_clusters, neo4j_session):
    """
    Test the full sync function to ensure clusters and topics are loaded correctly
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act - Use the sync function instead of calling load directly
    cartography.intel.aws.elasticache.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert Elasticache clusters exist with correct properties
    # Note: id and arn fields are the ARN, cache_cluster_id is the cluster ID
    assert check_nodes(
        neo4j_session, "AWSElasticacheCluster", ["id", "arn", "cache_cluster_id"]
    ) == {
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-001",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-001",
            "test-group-0001-001",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-002",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-002",
            "test-group-0001-002",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-001",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-001",
            "test-group-0002-001",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-002",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-002",
            "test-group-0002-002",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0003-001",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0003-001",
            "test-group-0003-001",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0004-001",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0004-001",
            "test-group-0004-001",
        ),
    }

    # Assert Elasticache topics exist
    assert check_nodes(neo4j_session, "AWSElasticacheTopic", ["id", "arn"]) == {
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
        ),
    }

    # Assert Elasticache clusters are connected to AWS account
    assert check_rels(
        neo4j_session,
        "AWSElasticacheCluster",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-001",
            "000000000000",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-002",
            "000000000000",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-001",
            "000000000000",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-002",
            "000000000000",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0003-001",
            "000000000000",
        ),
        (
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0004-001",
            "000000000000",
        ),
    }

    # Assert Elasticache topics are connected to AWS account
    assert check_rels(
        neo4j_session,
        "AWSElasticacheTopic",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:sns:us-east-1:123456789000:elasticache-events", "000000000000"),
    }

    # Assert Elasticache topics are connected to clusters (CACHE_CLUSTER relationship)
    assert check_rels(
        neo4j_session,
        "AWSElasticacheTopic",
        "id",
        "AWSElasticacheCluster",
        "id",
        "CACHE_CLUSTER",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-001",
        ),
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-002",
        ),
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-001",
        ),
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0002-002",
        ),
        (
            "arn:aws:sns:us-east-1:123456789000:elasticache-events",
            "arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0003-001",
        ),
    }

    # Verify that clusters have the expected properties
    assert check_nodes(
        neo4j_session,
        "AWSElasticacheCluster",
        ["cache_cluster_id", "engine", "cache_node_type", "cache_cluster_status"],
    ) == {
        ("test-group-0001-001", "redis", "cache.t3.medium", "available"),
        ("test-group-0001-002", "redis", "cache.t3.medium", "available"),
        ("test-group-0002-001", "redis", "cache.t3.medium", "available"),
        ("test-group-0002-002", "redis", "cache.t3.medium", "available"),
        ("test-group-0003-001", "redis", "cache.t3.medium", "available"),
        ("test-group-0004-001", "redis", "cache.t3.medium", "available"),
    }

    # Verify that topics have the expected properties
    assert check_nodes(neo4j_session, "AWSElasticacheTopic", ["id", "status"]) == {
        ("arn:aws:sns:us-east-1:123456789000:elasticache-events", "active"),
    }
