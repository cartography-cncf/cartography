import json
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import cartography.intel.aws.ecr
import cartography.intel.trivy
import tests.data.aws.ecr
from cartography.intel.trivy import sync_trivy_aws_ecr_from_dir
from tests.data.trivy.trivy_sample import TRIVY_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.cartography.intel.trivy.test_helpers import (
    assert_all_trivy_relationships,
)
from tests.integration.cartography.intel.trivy.test_helpers import assert_trivy_findings
from tests.integration.cartography.intel.trivy.test_helpers import assert_trivy_packages

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(TRIVY_SAMPLE),
)
@patch.object(
    cartography.intel.trivy,
    "get_json_files_in_dir",
    return_value={"/tmp/scan.json"},
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=tests.data.aws.ecr.DESCRIBE_REPOSITORIES["repositories"][
        2:
    ],  # just the test-repository,
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=tests.data.aws.ecr.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository"
    ][
        :1
    ],  # just one image
)
def test_sync_trivy_aws_ecr(
    mock_get_images,
    mock_get_repos,
    mock_list_dir_scan_results,
    mock_file_open,
    neo4j_session,
):
    """
    Ensure that Trivy scan results are properly loaded into Neo4j
    """
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # First sync ECR data
    boto3_session = MagicMock()
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act
    sync_trivy_aws_ecr_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert using shared helpers
    assert_trivy_findings(neo4j_session)
    assert_trivy_packages(neo4j_session)
    assert_all_trivy_relationships(neo4j_session)
