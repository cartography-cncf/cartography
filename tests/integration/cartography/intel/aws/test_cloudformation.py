from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudformation
import tests.data.aws.cloudformation
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = tests.data.aws.cloudformation.TEST_ACCOUNT_ID
TEST_REGION = tests.data.aws.cloudformation.TEST_REGION
TEST_UPDATE_TAG = tests.data.aws.cloudformation.TEST_UPDATE_TAG


@patch.object(
    cartography.intel.aws.cloudformation,
    "get_cloudformation_stacks",
    return_value=tests.data.aws.cloudformation.DESCRIBE_STACKS,
)
def test_sync_cloudformation_stacks(mock_get_stacks, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create a mock AWSRole for the relationship test
    neo4j_session.run(
        "MERGE (r:AWSRole {arn: $arn})",
        arn=f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
    )

    # Act
    cartography.intel.aws.cloudformation.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Check nodes were created with correct properties
    assert check_nodes(
        neo4j_session,
        "CloudFormationStack",
        ["id", "stack_name", "stack_status", "role_arn"],
    ) == {
        (
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-1/11111111-1111-1111-1111-111111111111",
            "test-stack-1",
            "CREATE_COMPLETE",
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
        ),
        (
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-2/22222222-2222-2222-2222-222222222222",
            "test-stack-2",
            "UPDATE_COMPLETE",
            None,
        ),
    }

    # Assert - Check AWSAccount relationship
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
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-1/11111111-1111-1111-1111-111111111111",
        ),
        (
            TEST_ACCOUNT_ID,
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-2/22222222-2222-2222-2222-222222222222",
        ),
    }

    # Assert - Check AWSRole relationship (only stack-1 has RoleARN)
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
            f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-1/11111111-1111-1111-1111-111111111111",
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
        ),
    }
