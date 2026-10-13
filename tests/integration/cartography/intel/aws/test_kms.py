from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

import cartography.intel.aws.kms
import tests.data.aws.kms
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_load_kms_keys(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_KEYS
    # Create policy data for test keys using defaults
    policy_data = {}
    for key in data:
        policy_data[key["KeyId"]] = {"anonymous_access": False, "anonymous_actions": []}
    transformed_data = cartography.intel.aws.kms.transform_kms_keys(data, policy_data)
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
            "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
            "9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        ),
    }

    assert check_nodes(neo4j_session, "AWSKMSKey", ["arn", "key_id"]) == expected_nodes


def test_load_kms_keys_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test KMS Key
    data = tests.data.aws.kms.DESCRIBE_KEYS
    # Create policy data for test keys using defaults
    policy_data = {}
    for key in data:
        policy_data[key["KeyId"]] = {"anonymous_access": False, "anonymous_actions": []}
    transformed_data = cartography.intel.aws.kms.transform_kms_keys(data, policy_data)
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_rels = {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSKMSKey",
            "arn",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )


def test_load_kms_key_aliases(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_ALIASES
    transformed_data = cartography.intel.aws.kms.transform_kms_aliases(data)
    cartography.intel.aws.kms.load_kms_aliases(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography", "Cartography-A"),
        ("arn:aws:kms:eu-west-1:000000000000:alias/key2-testing", "Prod-Testing"),
    }

    assert (
        check_nodes(neo4j_session, "AWSKMSAlias", ["arn", "alias_name"])
        == expected_nodes
    )


def test_load_kms_key_aliases_relationships(neo4j_session):
    # Load Test KMS Key
    data_kms = tests.data.aws.kms.DESCRIBE_KEYS
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        data_kms,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test KMS Key Aliases
    data_alias = tests.data.aws.kms.DESCRIBE_ALIASES
    transformed_aliases = cartography.intel.aws.kms.transform_kms_aliases(data_alias)
    cartography.intel.aws.kms.load_kms_aliases(
        neo4j_session,
        transformed_aliases,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_rels = {
        (
            "arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            "arn:aws:kms:eu-west-1:000000000000:alias/key2-testing",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "AWSKMSAlias",
            "arn",
            "AWSKMSKey",
            "arn",
            "KNOWN_AS",
            rel_direction_right=True,
        )
        == expected_rels
    )


def test_load_kms_key_grants(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_GRANTS
    transformed_data = cartography.intel.aws.kms.transform_kms_grants(data)
    cartography.intel.aws.kms.load_kms_grants(
        neo4j_session,
        transformed_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("key-consolepolicy-3",),
    }

    assert check_nodes(neo4j_session, "AWSKMSGrant", ["grant_id"]) == expected_nodes


def test_load_kms_key_grants_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load test KMS Keys
    data_kms = tests.data.aws.kms.DESCRIBE_KEYS
    # Create policy data for test keys using defaults
    policy_data = {}
    for key in data_kms:
        policy_data[key["KeyId"]] = {"anonymous_access": False, "anonymous_actions": []}
    transformed_keys = cartography.intel.aws.kms.transform_kms_keys(
        data_kms, policy_data
    )
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        transformed_keys,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test KMS Key Grants
    data_grants = tests.data.aws.kms.DESCRIBE_GRANTS
    transformed_grants = cartography.intel.aws.kms.transform_kms_grants(data_grants)
    cartography.intel.aws.kms.load_kms_grants(
        neo4j_session,
        transformed_grants,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_rels = {
        (
            "key-consolepolicy-3",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "AWSKMSGrant",
            "grant_id",
            "AWSKMSKey",
            "arn",
            "APPLIED_ON",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.aws.kms,
    "get_kms_key_list",
    return_value=tests.data.aws.kms.DESCRIBE_KEYS,
)
def test_sync_kms_keys_when_list_aliases_is_denied(mock_get_keys, neo4j_session):
    """
    A role that may list keys but not their aliases still syncs the keys. Only the
    aliases are missing.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSKMSKey OR n:AWSKMSAlias OR n:AWSKMSGrant DETACH DELETE n"
    )
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    denied = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "ListAliases",
    )
    client = MagicMock()
    client.get_key_policy.side_effect = denied
    client.get_paginator.return_value.paginate.side_effect = denied
    boto3_session = MagicMock()
    boto3_session.client.return_value = client

    # Act
    cartography.intel.aws.kms.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSKMSKey", ["id"]) == {
        (key["KeyId"],) for key in tests.data.aws.kms.DESCRIBE_KEYS
    }
    assert check_nodes(neo4j_session, "AWSKMSAlias", ["id"]) == set()


@patch.object(
    cartography.intel.aws.kms,
    "get_kms_key_list",
    return_value=tests.data.aws.kms.DESCRIBE_KEYS,
)
def test_sync_kms_keeps_aliases_when_list_aliases_is_denied(
    mock_get_keys, neo4j_session
):
    """
    A denied alias list is incomplete, not empty, so the sync keeps the aliases that an
    earlier sync loaded instead of cleaning them up.
    """
    # Arrange
    neo4j_session.run(
        "MATCH (n) WHERE n:AWSKMSKey OR n:AWSKMSAlias OR n:AWSKMSGrant DETACH DELETE n"
    )
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.kms.load_kms_aliases(
        neo4j_session,
        cartography.intel.aws.kms.transform_kms_aliases(
            tests.data.aws.kms.DESCRIBE_ALIASES,
        ),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    denied = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "ListAliases",
    )
    client = MagicMock()
    client.get_key_policy.side_effect = denied
    client.get_paginator.return_value.paginate.side_effect = denied
    boto3_session = MagicMock()
    boto3_session.client.return_value = client
    new_update_tag = TEST_UPDATE_TAG + 1
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, new_update_tag)

    # Act
    cartography.intel.aws.kms.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        new_update_tag,
        {"UPDATE_TAG": new_update_tag, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSKMSAlias", ["id"]) == {
        (alias["AliasArn"],) for alias in tests.data.aws.kms.DESCRIBE_ALIASES
    }
