import copy
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
)
def test_sync_cloudformation_stacks(mock_get_stacks, neo4j_session):
    # Arrange: Prevent test data leakage by returning a deepcopy of the fixture
    mock_get_stacks.return_value = copy.deepcopy(
        tests.data.aws.cloudformation.DESCRIBE_STACKS
    )

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


def test_cleanup_cloudformation_stacks(neo4j_session):
    # Arrange: Create account and load a stack through the normal load path
    from datetime import datetime
    from datetime import timezone

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    stale_stack_id = (
        "arn:aws:cloudformation:us-east-1:000000000000:stack/stale-stack/old-uuid"
    )
    stale_stack_data = [
        {
            "StackId": stale_stack_id,
            "StackName": "stale-stack",
            "StackStatus": "CREATE_COMPLETE",
            "CreationTime": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "Tags": None,
        },
    ]
    cartography.intel.aws.cloudformation.load_cloudformation_stacks(
        neo4j_session,
        stale_stack_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Pre-assert: stale node exists
    pre = neo4j_session.run(
        "MATCH (s:CloudFormationStack {id: $id}) RETURN s",
        id=stale_stack_id,
    ).data()
    assert len(pre) == 1

    # Act: Run cleanup with a newer tag (simulates next sync cycle)
    cartography.intel.aws.cloudformation.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: Stale node should be gone
    post = neo4j_session.run(
        "MATCH (s:CloudFormationStack {id: $id}) RETURN s",
        id=stale_stack_id,
    ).data()
    assert len(post) == 0
