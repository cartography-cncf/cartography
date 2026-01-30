import copy
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
    return_value=copy.deepcopy(tests.data.aws.secretsmanager.LIST_SECRETS),
)
@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_versions",
    return_value=copy.deepcopy(tests.data.aws.secretsmanager.LIST_SECRET_VERSIONS),
)
def test_sync_secretsmanager(mock_get_versions, mock_get_secrets, neo4j_session):
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


@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_list",
    return_value=copy.deepcopy(tests.data.aws.secretsmanager.LIST_SECRETS[:1]),
)
@patch.object(
    cartography.intel.aws.secretsmanager, "get_secret_versions", return_value=[]
)
def test_sync_secretsmanager_no_versions(
    mock_get_versions, mock_get_secrets, neo4j_session
):
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
        ["name"],
    ) == {
        ("test-secret-1",),
    }

    assert (
        check_nodes(
            neo4j_session,
            "SecretsManagerSecretVersion",
            ["arn"],
        )
        == set()
    )


@patch("cartography.util.dict_date_to_epoch")
@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_list",
    return_value=copy.deepcopy(tests.data.aws.secretsmanager.LIST_SECRETS[:1]),
)
@patch.object(
    cartography.intel.aws.secretsmanager,
    "get_secret_versions",
    return_value=copy.deepcopy(tests.data.aws.secretsmanager.LIST_SECRET_VERSIONS[:1]),
)
def test_secret_version_kms_key_relationship(
    mock_get_versions, mock_get_secrets, mock_dict_date, neo4j_session
):
    mock_dict_date.side_effect = lambda obj, key: (
        int(obj.get(key).timestamp())
        if obj.get(key) and hasattr(obj.get(key), "timestamp")
        else obj.get(key)
    )

    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run(
        """
        MERGE (k:AWSKMSKey{id: $key_id})
        ON CREATE SET k.firstseen = timestamp()
        SET k.arn = $key_arn,
            k.region = $region,
            k.lastupdated = $update_tag
    """,
        key_id="arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
        key_arn="arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
        region=TEST_REGION,
        update_tag=TEST_UPDATE_TAG,
    )

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

    assert check_rels(
        neo4j_session,
        "SecretsManagerSecretVersion",
        "arn",
        "AWSKMSKey",
        "id",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
            "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
        ),
    }
