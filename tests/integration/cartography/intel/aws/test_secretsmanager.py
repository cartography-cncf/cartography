from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.secretsmanager
import tests.data.aws.secretsmanager
from cartography.intel.aws.secretsmanager import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_list",
    return_value=tests.data.aws.secretsmanager.LIST_SECRETS,
)
@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_versions",
    return_value=tests.data.aws.secretsmanager.LIST_SECRET_VERSIONS,
)
def test_sync_secretsmanager(mock_get_versions, mock_get_secrets, neo4j_session):
    """
    Test that Secrets Manager secrets and their versions are correctly synced to the graph.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:SecretsManagerSecret) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SecretsManagerSecretVersion) DETACH DELETE n")

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
        "SecretsManagerSecret",
        [
            "arn",
            "name",
            "rotation_enabled",
            "kms_key_id",
            "region",
        ],
    ) == {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "test-secret-1",
            True,
            "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
            "us-east-1",
        ),
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-2-000000",
            "test-secret-2",
            False,
            None,
            "us-east-1",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "SecretsManagerSecretVersion",
        [
            "arn",
            "secret_id",
            "version_id",
        ],
    ) == {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "00000000-0000-0000-0000-000000000000",
        ),
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:11111111-1111-1111-1111-111111111111",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "11111111-1111-1111-1111-111111111111",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SecretsManagerSecret",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-2-000000",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SecretsManagerSecretVersion",
        "arn",
        "SecretsManagerSecret",
        "arn",
        "VERSION_OF",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        ),
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:11111111-1111-1111-1111-111111111111",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        ),
    }


@patch("cartography.util.dict_date_to_epoch", return_value=None)
@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_list",
    return_value=[
        {
            "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "Name": "test-secret-1",
            "Description": "Test secret",
            "RotationEnabled": False,
            "DeletedDate": None,
            "LastChangedDate": None,
            "LastAccessedDate": None,
            "LastRotatedDate": None,
            "CreatedDate": None,
        }
    ],
)
@patch.object(
    cartography.intel.aws.secretsmanager, "get_secret_versions", return_value=[]
)
def test_sync_secretsmanager_no_versions(
    mock_get_versions, mock_get_secrets, mock_date_to_epoch, neo4j_session
):
    """
    Test that when secrets exist but have no versions, no version nodes are created.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:SecretsManagerSecret) DETACH DELETE n")
    neo4j_session.run("MATCH (n:SecretsManagerSecretVersion) DETACH DELETE n")

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    secrets = neo4j_session.run(
        """
        MATCH (n:SecretsManagerSecret) RETURN count(n) as count
        """
    )
    assert secrets.single()["count"] > 0

    versions = neo4j_session.run(
        """
        MATCH (n:SecretsManagerSecretVersion) RETURN count(n) as count
        """
    )
    assert versions.single()["count"] == 0
