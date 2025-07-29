import cartography.intel.aws.kms
import tests.data.aws.kms
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

    assert check_nodes(neo4j_session, "KMSKey", ["arn", "key_id"]) == expected_nodes


def test_load_kms_keys_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
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
            "KMSKey",
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
        check_nodes(neo4j_session, "KMSAlias", ["arn", "alias_name"]) == expected_nodes
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
            "KMSAlias",
            "arn",
            "KMSKey",
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

    assert check_nodes(neo4j_session, "KMSGrant", ["grant_id"]) == expected_nodes


def test_load_kms_key_grants_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
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
            "KMSGrant",
            "grant_id",
            "KMSKey",
            "arn",
            "APPLIED_ON",
            rel_direction_right=True,
        )
        == expected_rels
    )
