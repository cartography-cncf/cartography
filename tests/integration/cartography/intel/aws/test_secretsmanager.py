import cartography.intel.aws.secretsmanager
import tests.data.aws.secretsmanager

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_load_secrets(neo4j_session, *args):
    """
    Ensure that expected secrets get loaded with their key fields.
    """
    data = tests.data.aws.secretsmanager.LIST_SECRETS
    cartography.intel.aws.secretsmanager.load_secrets(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "test-secret-1",
            True,
            90,
            "arn:aws:lambda:us-east-1:000000000000:function:test-secret-rotate",
            "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
            "us-west-1",
            "us-east-1",
            1397672089,
        ),
        (
            "test-secret-2",
            False,
            None,
            None,
            None,
            None,
            "us-east-1",
            1397672089,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:SecretsManagerSecret)
        RETURN s.name, s.rotation_enabled, s.rotation_rules_automatically_after_days,
        s.rotation_lambda_arn, s.kms_key_id, s.primary_region, s.region, s.last_changed_date
        """,
    )
    actual_nodes = {
        (
            n["s.name"],
            n["s.rotation_enabled"],
            n["s.rotation_rules_automatically_after_days"],
            n["s.rotation_lambda_arn"],
            n["s.kms_key_id"],
            n["s.primary_region"],
            n["s.region"],
            n["s.last_changed_date"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
