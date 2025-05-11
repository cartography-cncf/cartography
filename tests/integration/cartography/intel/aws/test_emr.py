import cartography.intel.aws.emr
import tests.data.aws.emr
from cartography.intel.aws.emr import cleanup
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_test_accounts(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )


def test_load_emr_clusters_nodes(neo4j_session):
    # Act
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",),
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",),
    }
    assert check_nodes(neo4j_session, "EMRCluster", ["arn"]) == expected_nodes


def test_load_emr_clusters_relationships(neo4j_session):
    _create_test_accounts(neo4j_session)

    # Act: Load Test EMR Clusters
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected = {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "EMRCluster",
            "arn",
            "RESOURCE",
        )
        == expected
    )


def test_cleanup_emr(neo4j_session):
    # Arrange: load EMR cluster data
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    _create_test_accounts(neo4j_session)
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Arrange: load in an unrelated EC2 instance. This should not be affected by the EMR module's cleanup job.
    neo4j_session.run(
        """
        MERGE (i:EC2Instance{id:1234, lastupdated: $lastupdated})<-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    # [Pre-test] Assert that the EMR clusters exist
    assert check_nodes(neo4j_session, "EMRCluster", ["arn"]) == {
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",),
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",),
    }
    # [Pre-test] Assert that the unrelated EC2 instance exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2Instance",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }

    # Act: run the cleanup job
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG
        + 1,  # Simulate a new sync run finished so the old update tag is obsolete now
        "AWS_ID": TEST_ACCOUNT_ID,
        # Add in extra params that may have been added by other modules.
        # Expectation: These should not affect cleanup job execution.
        "permission_relationships_file": "/path/to/perm/rels/file",
        "OKTA_ORG_ID": "my-org-id",
    }
    cleanup(neo4j_session, common_job_parameters)

    # Assert: Expect no EMR clusters in the graph now
    assert check_nodes(neo4j_session, "EMRCluster", ["arn"]) == set()
    # Assert: Expect that the unrelated EC2 instance was not touched by the cleanup job
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2Instance",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }
