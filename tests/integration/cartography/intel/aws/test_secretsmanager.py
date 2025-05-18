import datetime
from datetime import timezone as tz

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


def test_load_secret_versions(neo4j_session, *args):
    """
    Ensure that expected secret versions get loaded with their key fields.
    """

    secret_data = [
        {
            "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "Name": "test-secret-1",
            "Description": "This is a test secret",
            "RotationEnabled": True,
            "RotationRules": {"AutomaticallyAfterDays": 90},
            "RotationLambdaARN": "arn:aws:lambda:us-east-1:000000000000:function:test-secret-rotate",
            "KmsKeyId": "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
            "CreatedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
            "LastRotatedDate": datetime.datetime(
                2014, 4, 16, 18, 14, 49, tzinfo=tz.utc
            ),
            "LastChangedDate": datetime.datetime(
                2014, 4, 16, 18, 14, 49, tzinfo=tz.utc
            ),
            "LastAccessedDate": datetime.datetime(
                2014, 4, 16, 18, 14, 49, tzinfo=tz.utc
            ),
            "PrimaryRegion": "us-west-1",
        }
    ]
    cartography.intel.aws.secretsmanager.load_secrets(
        neo4j_session,
        secret_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.secretsmanager.LIST_SECRET_VERSIONS
    cartography.intel.aws.secretsmanager.load_secret_versions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "00000000-0000-0000-0000-000000000000",
            ("AWSCURRENT",),
            "us-east-1",
            1397672089,
        ),
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:11111111-1111-1111-1111-111111111111",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
            "11111111-1111-1111-1111-111111111111",
            ("AWSPREVIOUS",),
            "us-east-1",
            1397585689,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (sv:SecretsManagerSecretVersion)
        RETURN sv.arn, sv.secret_id, sv.version_id, sv.version_stages, sv.region, sv.created_date
        """,
    )
    actual_nodes = {
        (
            n["sv.arn"],
            n["sv.secret_id"],
            n["sv.version_id"],
            tuple(n["sv.version_stages"]),
            n["sv.region"],
            n["sv.created_date"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    relationships = neo4j_session.run(
        """
        MATCH (sv:SecretsManagerSecretVersion)-[r:VERSION_OF]->(s:SecretsManagerSecret)
        RETURN sv.arn, s.arn
        """,
    )
    actual_relationships = {(r["sv.arn"], r["s.arn"]) for r in relationships}
    expected_relationships = {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        ),
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:11111111-1111-1111-1111-111111111111",
            "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        ),
    }
    assert actual_relationships == expected_relationships
