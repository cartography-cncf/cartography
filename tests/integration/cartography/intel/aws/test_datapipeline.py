from unittest.mock import patch

import cartography.intel.aws.datapipeline
from tests.data.aws.datapipeline import DESCRIBE_PIPELINES_RESPONSE
from tests.data.aws.datapipeline import LIST_PIPELINES_RESPONSE
from tests.data.aws.datapipeline import TEST_ACCOUNT_ID
from tests.data.aws.datapipeline import TEST_REGION
from tests.data.aws.datapipeline import TEST_UPDATE_TAG
from tests.data.aws.datapipeline import TRANSFORMED_PIPELINES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_load_datapipeline_pipelines_nodes(neo4j_session):
    """Test that Data Pipeline nodes are created correctly."""
    # Act
    cartography.intel.aws.datapipeline.load_datapipeline_pipelines(
        neo4j_session,
        TRANSFORMED_PIPELINES,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("df-1234567890", "test-pipeline-1"),
        ("df-0987654321", "test-pipeline-2"),
    }
    assert check_nodes(neo4j_session, "DataPipeline", ["id", "name"]) == expected_nodes


def test_load_datapipeline_pipelines_relationships(neo4j_session):
    """Test that Data Pipeline relationships to AWS Account are created correctly."""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act: Load Test Data Pipelines
    cartography.intel.aws.datapipeline.load_datapipeline_pipelines(
        neo4j_session,
        TRANSFORMED_PIPELINES,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected = {
        ("df-1234567890", TEST_ACCOUNT_ID),
        ("df-0987654321", TEST_ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "DataPipeline",
            "id",
            "AWSAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,  # (:DataPipeline)<-[:RESOURCE]-(:AWSAccount)
        )
        == expected
    )


@patch.object(
    cartography.intel.aws.datapipeline,
    "get_datapipeline_pipelines",
    return_value=["df-1234567890", "df-0987654321"],
)
@patch.object(
    cartography.intel.aws.datapipeline,
    "get_datapipeline_pipeline_details",
    return_value=DESCRIBE_PIPELINES_RESPONSE["pipelineDescriptionList"],
)
def test_sync_datapipeline_pipelines(mock_get_details, mock_get_pipelines, neo4j_session):
    """Test the full sync function for Data Pipelines."""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act: Run sync
    cartography.intel.aws.datapipeline.sync(
        neo4j_session,
        None,  # boto3_session is mocked
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: Verify nodes were created
    expected_nodes = {
        ("df-1234567890", "test-pipeline-1"),
        ("df-0987654321", "test-pipeline-2"),
    }
    assert check_nodes(neo4j_session, "DataPipeline", ["id", "name"]) == expected_nodes

    # Assert: Verify relationships were created
    expected_rels = {
        ("df-1234567890", TEST_ACCOUNT_ID),
        ("df-0987654321", TEST_ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "DataPipeline",
            "id",
            "AWSAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


def test_cleanup_datapipeline(neo4j_session):
    """Test that cleanup removes stale Data Pipeline nodes."""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Arrange: Load Data Pipeline data
    cartography.intel.aws.datapipeline.load_datapipeline_pipelines(
        neo4j_session,
        TRANSFORMED_PIPELINES,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Load an unrelated EC2 instance. This should not be affected by cleanup.
    neo4j_session.run(
        """
        MERGE (i:EC2Instance{id: "i-12345", lastupdated: $lastupdated})<-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    # [Pre-test] Assert that the Data Pipelines exist
    assert check_nodes(neo4j_session, "DataPipeline", ["id"]) == {
        ("df-1234567890",),
        ("df-0987654321",),
    }

    # [Pre-test] Assert that the unrelated EC2 instance exists
    assert check_rels(
        neo4j_session,
        "EC2Instance",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:EC2Instance)<-[:RESOURCE]-(:AWSAccount)
    ) == {
        ("i-12345", TEST_ACCOUNT_ID),
    }

    # Act: Run the cleanup job with a new update tag
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,  # Simulate a new sync run
        "AWS_ID": TEST_ACCOUNT_ID,
    }
    cartography.intel.aws.datapipeline.cleanup(neo4j_session, common_job_parameters)

    # Assert: Expect no Data Pipelines in the graph now
    assert check_nodes(neo4j_session, "DataPipeline", ["id"]) == set()

    # Assert: Expect that the unrelated EC2 instance was not touched by cleanup
    assert check_rels(
        neo4j_session,
        "EC2Instance",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,  # (:EC2Instance)<-[:RESOURCE]-(:AWSAccount)
    ) == {
        ("i-12345", TEST_ACCOUNT_ID),
    }
