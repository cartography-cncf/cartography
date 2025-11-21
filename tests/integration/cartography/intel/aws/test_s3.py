import cartography.intel.aws.s3
import cartography.intel.aws.sns
import tests.data.aws.s3
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_s3_buckets(neo4j_session, *args):
    """
    Ensure that expected buckets get loaded with their key fields.
    """
    data = tests.data.aws.s3.LIST_BUCKETS
    cartography.intel.aws.s3.load_s3_buckets(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "bucket-1",
            "bucket-1",
            "eu-west-1",
        ),
        (
            "bucket-2",
            "bucket-2",
            "me-south-1",
        ),
        (
            "bucket-3",
            "bucket-3",
            None,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket) return s.id, s.name, s.region
        """,
    )
    actual_nodes = {
        (
            n["s.id"],
            n["s.name"],
            n["s.region"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_s3_encryption(neo4j_session, *args):
    """
    Ensure that expected bucket gets loaded with their encryption fields.
    """
    data = tests.data.aws.s3.GET_ENCRYPTION
    cartography.intel.aws.s3._load_s3_encryption(neo4j_session, data, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            "bucket-1",
            True,
            "aws:kms",
            "arn:aws:kms:eu-east-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
            False,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket)
        WHERE s.id = 'bucket-1'
        RETURN s.id, s.default_encryption, s.encryption_algorithm, s.encryption_key_id, s.bucket_key_enabled
        """,
    )
    actual_nodes = {
        (
            n["s.id"],
            n["s.default_encryption"],
            n["s.encryption_algorithm"],
            n["s.encryption_key_id"],
            n["s.bucket_key_enabled"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_s3_policies(neo4j_session, *args):
    """
    Ensure that expected bucket policy statements are loaded with their key fields.
    """
    data = cartography.intel.aws.s3.parse_policy_statements(
        "bucket-1",
        tests.data.aws.s3.LIST_STATEMENTS,
    )
    cartography.intel.aws.s3._load_s3_policy_statements(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = [
        (
            "S3PolicyId1",
            "2012-10-17",
            "bucket-1/policy_statement/1/IPAllow",
            "IPAllow",
            "Deny",
            '"*"',
            "s3:*",
            [
                "arn:aws:s3:::DOC-EXAMPLE-BUCKET",
                "arn:aws:s3:::DOC-EXAMPLE-BUCKET/*",
            ],
            '{"NotIpAddress": {"aws:SourceIp": "54.240.143.0/24"}}',
        ),
        (
            "S3PolicyId1",
            "2012-10-17",
            "bucket-1/policy_statement/2/S3PolicyId2",
            "S3PolicyId2",
            "Deny",
            '"*"',
            "s3:*",
            "arn:aws:s3:::DOC-EXAMPLE-BUCKET/taxdocuments/*",
            '{"Null": {"aws:MultiFactorAuthAge": true}}',
        ),
        (
            "S3PolicyId1",
            "2012-10-17",
            "bucket-1/policy_statement/3/",
            "",
            "Allow",
            '"*"',
            ["s3:GetObject"],
            "arn:aws:s3:::DOC-EXAMPLE-BUCKET/*",
            None,
        ),
    ]

    nodes = neo4j_session.run(
        """
        MATCH (s:S3PolicyStatement)
        WHERE s.bucket = 'bucket-1'
        RETURN
        s.policy_id, s.policy_version, s.id, s.sid, s.effect, s.principal, s.action, s.resource, s.condition
        """,
    )
    actual_nodes = [
        (
            n["s.policy_id"],
            n["s.policy_version"],
            n["s.id"],
            n["s.sid"],
            n["s.effect"],
            n["s.principal"],
            n["s.action"],
            n["s.resource"],
            n["s.condition"],
        )
        for n in nodes
    ]
    assert len(actual_nodes) == 3
    for node in actual_nodes:
        assert node in expected_nodes

    actual_relationships = neo4j_session.run(
        """
        MATCH (:S3Bucket{id:"bucket-1"})-[r:POLICY_STATEMENT]->(:S3PolicyStatement) RETURN count(r)
        """,
    )

    assert actual_relationships.single().value() == 3


def test_load_s3_bucket_ownership(neo4j_session, *args):
    """
    Ensure that expected bucket gets loaded with their bucket ownership controls fields.
    """
    data = tests.data.aws.s3.GET_BUCKET_OWNERSHIP_CONTROLS
    cartography.intel.aws.s3._load_bucket_ownership_controls(
        neo4j_session, data, TEST_UPDATE_TAG
    )

    expected_nodes = {
        (
            "bucket-1",
            "BucketOwnerPreferred",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket)
        WHERE s.id = 'bucket-1'
        RETURN s.id, s.object_ownership
        """,
    )
    actual_nodes = {
        (
            n["s.id"],
            n["s.object_ownership"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_s3_sns_relationship(neo4j_session):
    """Test that S3 bucket to SNS topic relationships are created correctly."""

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.s3.load_s3_buckets(
        neo4j_session,
        tests.data.aws.s3.LIST_BUCKETS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.sns.load_sns_topics(
        neo4j_session,
        tests.data.aws.s3.SNS_TOPICS,
        "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    parsed_notifications = cartography.intel.aws.s3.parse_notification_configuration(
        "bucket-1",
        tests.data.aws.s3.S3_NOTIFICATIONS,
    )

    cartography.intel.aws.s3._load_s3_notifications(
        neo4j_session,
        parsed_notifications,
        TEST_UPDATE_TAG,
    )

    assert check_rels(
        neo4j_session,
        "S3Bucket",
        "id",
        "SNSTopic",
        "arn",
        "NOTIFIES",
        rel_direction_right=True,
    ) == {
        ("bucket-1", "arn:aws:sns:us-east-1:123456789012:test-topic"),
    }


def test_load_s3_bucket_logging(neo4j_session):
    """
    Ensure that expected bucket gets loaded with their bucket logging fields.
    """
    # Test enabled logging
    # Arrange
    parsed_data_enabled = cartography.intel.aws.s3.parse_bucket_logging(
        "bucket-1", tests.data.aws.s3.GET_BUCKET_LOGGING_ENABLED
    )
    expected_nodes_enabled = {
        (
            parsed_data_enabled["bucket"],
            parsed_data_enabled["logging_enabled"],
            parsed_data_enabled["target_bucket"],
        ),
    }

    # Act
    cartography.intel.aws.s3._load_bucket_logging(
        neo4j_session, [parsed_data_enabled], TEST_UPDATE_TAG
    )

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket)
        WHERE s.name = 'bucket-1'
        RETURN s.name, s.logging_enabled, s.logging_target_bucket
        """,
    )
    actual_nodes = {
        (
            n["s.name"],
            n["s.logging_enabled"],
            n["s.logging_target_bucket"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes_enabled

    # Test disabled logging
    # Arrange
    parsed_data_disabled = cartography.intel.aws.s3.parse_bucket_logging(
        "bucket-2", tests.data.aws.s3.GET_BUCKET_LOGGING_DISABLED
    )
    expected_nodes_disabled = {
        (
            parsed_data_disabled["bucket"],
            parsed_data_disabled["logging_enabled"],
            parsed_data_disabled["target_bucket"],
        ),
    }

    # Act
    cartography.intel.aws.s3._load_bucket_logging(
        neo4j_session, [parsed_data_disabled], TEST_UPDATE_TAG
    )

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket)
        WHERE s.name = 'bucket-2'
        RETURN s.name, s.logging_enabled, s.logging_target_bucket
        """,
    )
    actual_nodes = {
        (
            n["s.name"],
            n["s.logging_enabled"],
            n["s.logging_target_bucket"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes_disabled
