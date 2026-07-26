from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apprunner
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


def _boto3_session_supporting_region() -> MagicMock:
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = [TEST_REGION]
    return boto3_session


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
    boto3_session = _boto3_session_supporting_region()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    expected_nodes = {
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",),
    }
    assert (
        check_nodes(neo4j_session, "AWSAppRunnerService", ["arn"]) == expected_nodes
    )
    # Compatibility alias from ExtraNodeLabels
    assert check_nodes(neo4j_session, "AppRunnerService", ["arn"]) == expected_nodes

    code_service_props = check_nodes(
        neo4j_session,
        "AWSAppRunnerService",
        ["arn", "code_repository_url"],
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
    boto3_session = _boto3_session_supporting_region()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _seed_roles(neo4j_session)

    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

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
            "AWSAppRunnerService",
            "arn",
            "RESOURCE",
        )
        == expected_account_rels
    )

    assert check_rels(
        neo4j_session,
        "AWSAppRunnerService",
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

    assert check_rels(
        neo4j_session,
        "AWSAppRunnerService",
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
    boto3_session = _boto3_session_supporting_region()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.apprunner.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    neo4j_session.run(
        """
        MERGE (i:AWSEC2Instance{id:1234, lastupdated: $lastupdated})
              <-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    assert check_nodes(neo4j_session, "AWSAppRunnerService", ["arn"]) == {
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-service/abc123",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-other-service/def456",),
        ("arn:aws:apprunner:us-east-1:123456789012:service/my-code-service/ghi789",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSEC2Instance",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "AWS_ID": TEST_ACCOUNT_ID,
        "permission_relationships_file": "/path/to/perm/rels/file",
        "OKTA_ORG_ID": "my-org-id",
    }
    cleanup(neo4j_session, common_job_parameters)

    assert check_nodes(neo4j_session, "AWSAppRunnerService", ["arn"]) == set()
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSEC2Instance",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }
