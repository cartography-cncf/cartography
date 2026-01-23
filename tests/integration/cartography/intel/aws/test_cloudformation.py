from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudformation
from cartography.intel.aws.cloudformation import sync
from tests.data.aws import cloudformation as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = test_data.TEST_ACCOUNT_ID
TEST_UPDATE_TAG = test_data.TEST_UPDATE_TAG
TEST_REGION = test_data.TEST_REGION


def _cleanup_cloudformation(neo4j_session):
    """Remove CloudFormation nodes from previous tests."""
    neo4j_session.run("MATCH (n:CloudFormationStack) DETACH DELETE n")


@patch.object(
    cartography.intel.aws.cloudformation,
    "get_cloudformation_stacks",
    return_value=test_data.CLOUDFORMATION_STACKS,
)
def test_sync_cloudformation(mock_get_stacks, neo4j_session):
    _cleanup_cloudformation(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run(
        "MERGE (:AWSRole {arn: $arn})",
        arn=f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "CloudFormationStack",
        ["id", "stack_name", "stack_status", "role_arn"],
    ) == {
        (
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack/12345678-90ab-cdef-1234-567890abcdef",
            "test-stack",
            "CREATE_COMPLETE",
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
        ),
        (
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/parent-stack/abcdef12-3456-7890-abcd-ef1234567890",
            "parent-stack",
            "UPDATE_COMPLETE",
            None,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CloudFormationStack",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack/12345678-90ab-cdef-1234-567890abcdef",
        ),
        (
            TEST_ACCOUNT_ID,
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/parent-stack/abcdef12-3456-7890-abcd-ef1234567890",
        ),
    }

    assert check_rels(
        neo4j_session,
        "CloudFormationStack",
        "id",
        "AWSRole",
        "arn",
        "HAS_EXECUTION_ROLE",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack/12345678-90ab-cdef-1234-567890abcdef",
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
        ),
    }
