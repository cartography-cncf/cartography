from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apprunner
import cartography.intel.aws.iam
import tests.data.aws.apprunner
from cartography.intel.aws.apprunner import cleanup
from cartography.intel.aws.iam import load_role_data
from cartography.intel.aws.iam import transform_role_trust_policies
from tests.data.aws.iam.roles import ROLES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _seed_roles(neo4j_session):
    transformed = transform_role_trust_policies(ROLES["Roles"], TEST_ACCOUNT_ID)
    load_role_data(
        neo4j_session,
        transformed.role_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.apprunner,
    "get_apprunner_services",
    return_value=tests.data.aws.apprunner.DESCRIBE_SERVICES,
)
def test_sync_apprunner_services_nodes(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    expected_nodes = {
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",),
    }
    assert check_nodes(neo4j_session, "AppRunnerService", ["arn"]) == expected_nodes

    # Code-source services should populate code_repository_url; image-source ones populate image_identifier.
    code_service_props = check_nodes(
        neo4j_session, "AppRunnerService", ["arn", "code_repository_url"]
    )
    assert (
        "arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",
        "https://github.com/example/my-code-service",
    ) in code_service_props


@patch.object(
    cartography.intel.aws.apprunner,
    "get_apprunner_services",
    return_value=tests.data.aws.apprunner.DESCRIBE_SERVICES,
)
def test_sync_apprunner_services_relationships(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _seed_roles(neo4j_session)

    # Act
    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: account owns each service
    expected_account_rels = {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AppRunnerService",
            "arn",
            "RESOURCE",
        )
        == expected_account_rels
    )

    # Assert: access role is linked for services with an AccessRoleArn
    assert check_rels(
        neo4j_session,
        "AppRunnerService",
        "arn",
        "AWSRole",
        "arn",
        "USES_ACCESS_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",
            "arn:aws:iam::1234:role/cartography-read-only",
        ),
        (
            "arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",
            "arn:aws:iam::1234:role/cartography-read-only",
        ),
    }

    # Assert: instance role is linked for every service (enables iam:PassRole privesc traversal)
    assert check_rels(
        neo4j_session,
        "AppRunnerService",
        "arn",
        "AWSRole",
        "arn",
        "USES_INSTANCE_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",
            "arn:aws:iam::1234:role/cartography-service",
        ),
        (
            "arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",
            "arn:aws:iam::1234:role/cartography-service",
        ),
        (
            "arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",
            "arn:aws:iam::1234:role/cartography-service",
        ),
    }


@patch.object(
    cartography.intel.aws.apprunner,
    "get_apprunner_services",
    return_value=tests.data.aws.apprunner.DESCRIBE_SERVICES,
)
def test_cleanup_apprunner(mock_get, neo4j_session):
    # Arrange: sync AppRunner service data
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    # Arrange: load in an unrelated EC2 instance. This should not be affected by the AppRunner module's cleanup job.
    neo4j_session.run(
        """
        MERGE (i:EC2Instance{id:1234, lastupdated: $lastupdated})<-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    # [Pre-test] Assert that the AppRunner services exist
    assert check_nodes(neo4j_session, "AppRunnerService", ["arn"]) == {
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",),
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

    # Assert: Expect no AppRunner services in the graph now
    assert check_nodes(neo4j_session, "AppRunnerService", ["arn"]) == set()
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
