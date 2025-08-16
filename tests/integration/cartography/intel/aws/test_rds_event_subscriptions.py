import cartography.intel.aws.rds
from tests.data.aws.rds import DESCRIBE_DBCLUSTERS_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBINSTANCES_RESPONSE
from tests.data.aws.rds import DESCRIBE_DBSNAPSHOTS_RESPONSE
from tests.data.aws.rds import DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE
from tests.data.aws.sns import TEST_RDS_EVENT_SUBSCRIPTION_TOPICS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account(neo4j_session):
    """Create test AWS account"""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)


def _ensure_local_neo4j_has_test_sns_topics(neo4j_session):
    """Create test SNS topics that event subscriptions can NOTIFY"""
    for topic_arn in TEST_RDS_EVENT_SUBSCRIPTION_TOPICS:
        neo4j_session.run(
            """
            MERGE (topic:SNSTopic{arn: $topic_arn})
            ON CREATE SET topic.firstseen = timestamp()
            SET topic.lastupdated = $update_tag
            """,
            topic_arn=topic_arn,
            update_tag=TEST_UPDATE_TAG,
        )


def _ensure_local_neo4j_has_test_rds_resources(neo4j_session):
    """Load test RDS sources"""
    # Load RDS instances
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        cartography.intel.aws.rds.transform_rds_instances(
            DESCRIBE_DBINSTANCES_RESPONSE["DBInstances"], TEST_REGION, TEST_ACCOUNT_ID
        ),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load RDS clusters
    cartography.intel.aws.rds.load_rds_clusters(
        neo4j_session,
        cartography.intel.aws.rds.transform_rds_clusters(
            DESCRIBE_DBCLUSTERS_RESPONSE["DBClusters"]
        ),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load RDS snapshots
    cartography.intel.aws.rds.load_rds_snapshots(
        neo4j_session,
        cartography.intel.aws.rds.transform_rds_snapshots(
            DESCRIBE_DBSNAPSHOTS_RESPONSE["DBSnapshots"]
        ),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_sync_rds_event_subscriptions(neo4j_session):
    """
    Test that RDS event subscriptions sync correctly and create proper nodes and relationships
    """
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_sns_topics(neo4j_session)
    _ensure_local_neo4j_has_test_rds_resources(neo4j_session)

    # Act
    transformed_subscriptions = (
        cartography.intel.aws.rds.transform_rds_event_subscriptions(
            DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        )
    )
    cartography.intel.aws.rds.load_rds_event_subscriptions(
        neo4j_session,
        transformed_subscriptions,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        (
            s["CustSubscriptionId"],
            s["EventSubscriptionArn"],
            s["SourceType"],
            s["Status"],
            s["Enabled"],
        )
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }
    actual_nodes = check_nodes(
        neo4j_session,
        "RDSEventSubscription",
        ["id", "arn", "source_type", "status", "enabled"],
    )
    assert actual_nodes == expected_nodes

    # RESOURCE
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "RDSEventSubscription",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, s["CustSubscriptionId"])
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }

    # NOTIFIES
    assert check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "SNSTopic",
        "arn",
        "NOTIFIES",
        rel_direction_right=True,
    ) == {
        (s["CustSubscriptionId"], s["SnsTopicArn"])
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }

    # MONITORS db_instance
    assert check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSInstance",
        "db_instance_identifier",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-instance"
        for id in s["SourceIdsList"]
    }

    # MONITORS db_cluster
    assert check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSCluster",
        "db_cluster_identifier",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-cluster"
        for id in s["SourceIdsList"]
    }

    # MONITORS db_snapshot
    assert check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSSnapshot",
        "db_snapshot_identifier",
        "MONITORS",
        rel_direction_right=True,
    ) == {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-snapshot"
        for id in s["SourceIdsList"]
    }
