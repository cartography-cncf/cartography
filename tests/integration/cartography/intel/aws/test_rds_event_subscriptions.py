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


def _ensure_local_neo4j_has_test_event_subscriptions(neo4j_session):
    """Load test RDS event subscriptions"""
    transformed = cartography.intel.aws.rds.transform_rds_event_subscriptions(
        DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    )
    cartography.intel.aws.rds.load_rds_event_subscriptions(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_event_subscription_properties(neo4j_session):
    """Test that RDS event subscription nodes have correct properties"""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_event_subscriptions(neo4j_session)

    # Test all three subscriptions
    for subscription in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]:
        result = neo4j_session.run(
            """
            MATCH (es:RDSEventSubscription {id: $subscription_id})
            RETURN es.customer_aws_id, es.sns_topic_arn, es.event_categories, es.source_ids
        """,
            subscription_id=subscription["CustSubscriptionId"],
        ).single()

        assert result["es.customer_aws_id"] == subscription["CustomerAwsId"]
        assert result["es.sns_topic_arn"] == subscription["SnsTopicArn"]
        expected_categories = (
            subscription["EventCategoriesList"]
            if subscription["EventCategoriesList"]
            else None
        )
        assert result["es.event_categories"] == expected_categories
        assert result["es.source_ids"] == subscription["SourceIdsList"]


def test_load_rds_event_subscriptions(neo4j_session):
    """Test that RDS event subscription nodes are loaded correctly"""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_event_subscriptions(neo4j_session)

    expected = {
        (
            s["CustSubscriptionId"],
            s["EventSubscriptionArn"],
            s["SourceType"],
            s["Status"],
            s["Enabled"],
        )
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }

    actual = check_nodes(
        neo4j_session,
        "RDSEventSubscription",
        ["id", "arn", "source_type", "status", "enabled"],
    )
    assert actual == expected


def test_load_event_subscription_relationships(neo4j_session):
    """Test that RDS event subscriptions create all expected relationships"""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_sns_topics(neo4j_session)
    _ensure_local_neo4j_has_test_rds_resources(neo4j_session)
    _ensure_local_neo4j_has_test_event_subscriptions(neo4j_session)

    # Test RESOURCE relationship to AWSAccount
    expected_account = {
        (TEST_ACCOUNT_ID, s["CustSubscriptionId"])
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }
    actual_account = check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "RDSEventSubscription",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_account == expected_account

    # Test NOTIFIES relationship to SNSTopic
    expected_sns = {
        (s["CustSubscriptionId"], s["SnsTopicArn"])
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
    }
    actual_sns = check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "SNSTopic",
        "arn",
        "NOTIFIES",
        rel_direction_right=True,
    )
    assert actual_sns == expected_sns

    # Test MONITORS relationship to RDSInstance
    expected_instances = {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-instance"
        for id in s["SourceIdsList"]
    }
    actual_instances = check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSInstance",
        "db_instance_identifier",
        "MONITORS",
        rel_direction_right=True,
    )
    assert actual_instances == expected_instances

    # Test MONITORS relationship to RDSCluster
    expected_clusters = {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-cluster"
        for id in s["SourceIdsList"]
    }
    actual_clusters = check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSCluster",
        "db_cluster_identifier",
        "MONITORS",
        rel_direction_right=True,
    )
    assert actual_clusters == expected_clusters

    # Test MONITORS relationship to RDSSnapshot
    expected_snapshots = {
        (s["CustSubscriptionId"], id)
        for s in DESCRIBE_EVENT_SUBSCRIPTIONS_RESPONSE["EventSubscriptionsList"]
        if s["SourceType"] == "db-snapshot"
        for id in s["SourceIdsList"]
    }
    actual_snapshots = check_rels(
        neo4j_session,
        "RDSEventSubscription",
        "id",
        "RDSSnapshot",
        "db_snapshot_identifier",
        "MONITORS",
        rel_direction_right=True,
    )
    assert actual_snapshots == expected_snapshots


def test_cleanup_event_subscriptions(neo4j_session):
    """Test that RDS event subscriptions are properly cleaned up"""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_event_subscriptions(neo4j_session)

    pre_cleanup = neo4j_session.run(
        "MATCH (es:RDSEventSubscription) RETURN count(es) as c"
    ).single()["c"]
    assert pre_cleanup > 0

    cartography.intel.aws.rds.cleanup_rds_event_subscriptions(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG - 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    post_cleanup = neo4j_session.run(
        "MATCH (es:RDSEventSubscription) RETURN count(es) as c"
    ).single()["c"]
    assert post_cleanup == 0
