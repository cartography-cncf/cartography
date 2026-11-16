import pytest

from cartography.intel.sentra import alerts
from cartography.intel.sentra.data_stores import aws_resource_ids
from tests.data.sentra import ALERTS

NO_IDS = {
    "aws_s3_bucket_name": None,
    "aws_rds_instance_arn": None,
    "aws_rds_cluster_arn": None,
    "aws_dynamodb_table_arn": None,
    "aws_redshift_cluster_arn": None,
}


@pytest.mark.parametrize(
    ("native_unique_id", "field", "expected"),
    [
        ("arn:aws:s3:::example-bucket", "aws_s3_bucket_name", "example-bucket"),
        (
            "arn:aws:rds:us-east-1:123456789012:db:orders",
            "aws_rds_instance_arn",
            "arn:aws:rds:us-east-1:123456789012:db:orders",
        ),
        (
            "arn:aws:rds:us-east-1:123456789012:cluster:orders",
            "aws_rds_cluster_arn",
            "arn:aws:rds:us-east-1:123456789012:cluster:orders",
        ),
        (
            "arn:aws:dynamodb:us-east-1:123456789012:table/sessions",
            "aws_dynamodb_table_arn",
            "arn:aws:dynamodb:us-east-1:123456789012:table/sessions",
        ),
        (
            "arn:aws:redshift:us-east-1:123456789012:cluster:warehouse",
            "aws_redshift_cluster_arn",
            "arn:aws:redshift:us-east-1:123456789012:cluster:warehouse",
        ),
        (
            "arn:aws-us-gov:s3:::gov-bucket",
            "aws_s3_bucket_name",
            "gov-bucket",
        ),
    ],
)
def test_aws_resource_ids_extracts_only_the_arn_resource_type(
    native_unique_id,
    field,
    expected,
):
    # Act
    ids = aws_resource_ids(native_unique_id, "AWS", None, "store-name")

    # Assert
    assert ids == {**NO_IDS, field: expected}


@pytest.mark.parametrize(
    "native_unique_id",
    [
        # An S3 object ARN is not a bucket.
        "arn:aws:s3:::example-bucket/path/to/object",
        # A DynamoDB stream ARN is not a table.
        "arn:aws:dynamodb:us-east-1:123456789012:table/sessions/stream/2026-01-01",
        # An RDS snapshot ARN is not an instance or cluster.
        "arn:aws:rds:us-east-1:123456789012:snapshot:orders-snap",
        # A service without a link stays unlinked.
        "arn:aws:es:us-east-1:123456789012:domain/search",
    ],
)
def test_aws_resource_ids_ignores_other_arn_resource_types(native_unique_id):
    # Act
    ids = aws_resource_ids(native_unique_id, "AWS", "s3", "store-name")

    # Assert
    assert ids == NO_IDS


def test_aws_resource_ids_uses_store_name_for_aws_s3_store_without_arn():
    # Act
    ids = aws_resource_ids(None, "AWS", "S3", "example-bucket")

    # Assert
    assert ids == {**NO_IDS, "aws_s3_bucket_name": "example-bucket"}


def test_aws_resource_ids_does_not_use_store_name_outside_aws_s3():
    # Act
    ids = [
        aws_resource_ids(None, "GCP", "gcs", "example-bucket"),
        aws_resource_ids(None, "AWS", "rds", "orders"),
        aws_resource_ids("projects/p/buckets/b", "GCP", "s3", "example-bucket"),
    ]

    # Assert
    assert ids == [NO_IDS, NO_IDS, NO_IDS]


def test_alert_transform_links_store_alert_to_store_only():
    # Arrange
    store_alert = ALERTS[0]

    # Act
    [transformed] = alerts.transform([store_alert])

    # Assert
    assert transformed["affected_data_store_id"] == store_alert["entity_id"]
    assert transformed["affected_aws_role_arn"] is None


@pytest.mark.parametrize(
    ("entity_type", "cloud_unique_id", "expected"),
    [
        (
            "IAM_ROLE",
            "arn:aws:iam::123456789012:role/data-pipeline",
            "arn:aws:iam::123456789012:role/data-pipeline",
        ),
        ("IAM_ROLE", "arn:aws:iam::123456789012:user/alice", None),
        ("IAM_ROLE", "data-pipeline", None),
        ("IAM_ROLE", None, None),
        ("IAM_GROUP", "arn:aws:iam::123456789012:role/data-pipeline", None),
    ],
)
def test_alert_transform_links_aws_role_only_for_iam_role_arn(
    entity_type,
    cloud_unique_id,
    expected,
):
    # Arrange
    alert = {
        **ALERTS[1],
        "entity_type": entity_type,
        "entity": {"name": "x", "owners": [], "cloud_unique_id": cloud_unique_id},
    }

    # Act
    [transformed] = alerts.transform([alert])

    # Assert
    assert transformed["affected_aws_role_arn"] == expected
    assert transformed["affected_data_store_id"] is None
