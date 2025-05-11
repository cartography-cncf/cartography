import cartography.intel.aws.kms
import tests.data.aws.kms

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_load_kms_keys(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_KEYS
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:KMSKey) RETURN r.arn;
        """,
    )
    actual_nodes = {n["r.arn"] for n in nodes}

    assert actual_nodes == expected_nodes


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
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:KMSKey) RETURN n1.id, n2.arn;
        """,
    )
    actual = {(r["n1.id"], r["n2.arn"]) for r in result}

    assert actual == expected


def test_load_kms_key_aliases(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_ALIASES
    cartography.intel.aws.kms._load_kms_key_aliases(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography",
        "arn:aws:kms:eu-west-1:000000000000:alias/key2-testing",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:KMSAlias) RETURN r.id;
        """,
    )
    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


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
    cartography.intel.aws.kms._load_kms_key_aliases(
        neo4j_session,
        data_alias,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            "arn:aws:kms:eu-west-1:000000000000:alias/key2-testing",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:KMSAlias)-[:KNOWN_AS]->(n2:KMSKey) RETURN n1.id, n2.arn;
        """,
    )
    actual = {(r["n1.id"], r["n2.arn"]) for r in result}

    assert actual == expected


def test_load_kms_key_grants(neo4j_session):
    data = tests.data.aws.kms.DESCRIBE_GRANTS
    cartography.intel.aws.kms._load_kms_key_grants(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "key-consolepolicy-3",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:KMSGrant) RETURN r.id;
        """,
    )
    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_kms_key_grants_relationships(neo4j_session):
    # Load Test KMS Key
    data_kms = tests.data.aws.kms.DESCRIBE_KEYS
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        data_kms,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test KMS Key Grants
    data_grants = tests.data.aws.kms.DESCRIBE_GRANTS
    cartography.intel.aws.kms._load_kms_key_grants(
        neo4j_session,
        data_grants,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "key-consolepolicy-3",
            "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:KMSGrant)-[:APPLIED_ON]->(n2:KMSKey) RETURN n1.id, n2.arn;
        """,
    )
    actual = {(r["n1.id"], r["n2.arn"]) for r in result}

    assert actual == expected
