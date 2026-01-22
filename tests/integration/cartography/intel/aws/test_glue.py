from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.glue
from cartography.intel.aws.glue import sync
from tests.data.aws.glue import GET_GLUE_CONNECTIONS_LIST
from tests.data.aws.glue import GET_GLUE_JOBS_LIST
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.glue,
    "get_glue_jobs",
    return_value=GET_GLUE_JOBS_LIST,
)
@patch.object(
    cartography.intel.aws.glue,
    "get_glue_connections",
    return_value=GET_GLUE_CONNECTIONS_LIST,
)
def test_sync_glue(
    mock_get_glue_connections,
    mock_get_glue_jobs,
    neo4j_session,
):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "GlueConnection", ["arn"]) == {
        ("test-jdbc-connection",),
    }

    assert check_nodes(neo4j_session, "GlueJob", ["arn"]) == {
        ("sample-etl-job",),
        ("sample-streaming-job",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "GlueConnection",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "test-jdbc-connection",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "GlueJob",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "sample-etl-job"),
        (TEST_ACCOUNT_ID, "sample-streaming-job"),
    }

    assert check_rels(
        neo4j_session,
        "GlueJob",
        "id",
        "GlueConnection",
        "id",
        "USES",
        rel_direction_right=True,
    ) == {
        ("sample-etl-job", "test-jdbc-connection"),
    }
