from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.datapipeline
from cartography.intel.aws.datapipeline import sync
from tests.data.aws.datapipeline import GET_DATAPIPELINE_PIPELINE_DETAILS
from tests.data.aws.datapipeline import GET_DATAPIPELINE_PIPELINE_ID_LIST
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.datapipeline,
    "get_datapipeline_pipeline_details",
    return_value=GET_DATAPIPELINE_PIPELINE_DETAILS,
)
@patch.object(
    cartography.intel.aws.datapipeline,
    "get_datapipeline_pipelines",
    return_value=GET_DATAPIPELINE_PIPELINE_ID_LIST,
)
def test_sync_datapipeline(
    mock_get_datapipeline_pipelines,
    mock_get_datapipeline_pipeline_details,
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
    expected_arns = {
        (
            "arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-06372391ZG65EXAMPLE",
        ),
        ("arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-01234567AB89EXAMPLE",),
    }
    assert check_nodes(neo4j_session, "DataPipeline", ["arn"]) == expected_arns

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "DataPipeline",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-06372391ZG65EXAMPLE",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:datapipeline:eu-west-1:000000000000:pipeline/df-01234567AB89EXAMPLE",
        ),
    }
