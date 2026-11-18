import pytest

from cartography.intel.sentra import alerts
from cartography.intel.sentra import data_classes
from cartography.intel.sentra import policies
from cartography.intel.sentra.data_stores import aws_resource_ids
from tests.data.sentra import ALERTS
from tests.data.sentra import DATA_CLASS_AWS_KEY_ID
from tests.data.sentra import DATA_CLASS_EMAIL_ID
from tests.data.sentra import DATA_CLASSES
from tests.data.sentra import POLICIES

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
    assert transformed["affected_data_store_ids"] == [store_alert["entity_id"]]
    assert transformed["affected_aws_role_arn"] is None
    assert transformed["violated_data_class_ids"] == []


def test_alert_transform_collects_stores_and_data_classes_of_violated_objects():
    # Arrange
    store_alert = {**ALERTS[0], "entity_id": "store-a"}
    violated_objects = {
        store_alert["id"]: [
            {
                "id": "object-1",
                "store_id": "store-a",
                "data_classes": [{"id": "class-2"}, {"id": "class-1"}],
            },
            {
                "id": "object-2",
                "store_id": "store-b",
                "data_classes": [{"id": "class-1"}],
            },
            {"id": "object-3", "store_id": "store-a", "data_classes": None},
        ],
    }

    # Act
    [transformed] = alerts.transform([store_alert], violated_objects)

    # Assert
    assert transformed["affected_data_store_ids"] == ["store-a", "store-b"]
    assert transformed["violated_data_class_ids"] == ["class-1", "class-2"]


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
    assert transformed["affected_data_store_ids"] == []


def test_policy_transform_flattens_affected_data_classes():
    # Arrange
    by_names, no_rules, by_categories = POLICIES

    # Act
    transformed = policies.transform([by_names, no_rules, by_categories])

    # Assert
    assert [
        (p["affected_data_classes"], p["affected_data_class_categories"])
        for p in transformed
    ] == [
        (["AWS Access Key"], []),
        ([], []),
        ([], ["Personal"]),
    ]


def test_policy_transform_resolves_data_class_names_and_categories_to_ids():
    # Arrange
    classes = data_classes.transform(DATA_CLASSES)
    by_names, no_rules, by_categories = POLICIES
    unknown_name = {
        **by_names,
        "affected_data_classes": {"categories": None, "data_classes": ["Passport"]},
    }

    # Act
    transformed = policies.transform(
        [by_names, no_rules, by_categories, unknown_name],
        classes,
    )

    # Assert
    assert [p["classification_data_class_ids"] for p in transformed] == [
        [DATA_CLASS_AWS_KEY_ID],
        [],
        [DATA_CLASS_EMAIL_ID],
        [],
    ]


def test_alert_transform_lists_aws_resources_of_affected_stores():
    # Arrange
    rds_instance_arn = "arn:aws:rds:us-east-1:123456789012:db:orders-primary"
    rds_cluster_arn = "arn:aws:rds:us-east-1:123456789012:cluster:orders"
    dynamodb_table_arn = "arn:aws:dynamodb:us-east-1:123456789012:table/orders"
    redshift_cluster_arn = "arn:aws:redshift:us-east-1:123456789012:cluster:analytics"
    store_alert = {**ALERTS[0], "entity_id": "store-bucket"}
    violated_objects = {
        store_alert["id"]: [
            {"id": f"object-{store}", "store_id": store, "data_classes": []}
            for store in (
                "store-rds-instance",
                "store-rds-cluster",
                "store-table",
                "store-warehouse",
                "store-saas",
            )
        ],
    }
    aws_ids_by_store = {
        "store-bucket": {"aws_s3_bucket_name": "example-bucket"},
        "store-rds-instance": {"aws_rds_instance_arn": rds_instance_arn},
        "store-rds-cluster": {"aws_rds_cluster_arn": rds_cluster_arn},
        "store-table": {"aws_dynamodb_table_arn": dynamodb_table_arn},
        "store-warehouse": {"aws_redshift_cluster_arn": redshift_cluster_arn},
    }

    # Act
    [transformed] = alerts.transform(
        [store_alert],
        violated_objects,
        aws_ids_by_store,
    )

    # Assert
    assert transformed["affected_aws_s3_bucket_names"] == ["example-bucket"]
    assert transformed["affected_aws_rds_instance_arns"] == [rds_instance_arn]
    assert transformed["affected_aws_rds_cluster_arns"] == [rds_cluster_arn]
    assert transformed["affected_aws_dynamodb_table_arns"] == [dynamodb_table_arn]
    assert transformed["affected_aws_redshift_cluster_arns"] == [
        redshift_cluster_arn,
    ]


def test_alert_transform_lists_no_aws_resources_for_stores_outside_aws():
    # Arrange
    store_alert = {**ALERTS[0], "entity_id": "store-saas"}

    # Act
    [transformed] = alerts.transform([store_alert], {}, {})

    # Assert
    assert transformed["affected_aws_s3_bucket_names"] == []
    assert transformed["affected_aws_rds_instance_arns"] == []
    assert transformed["affected_aws_rds_cluster_arns"] == []
    assert transformed["affected_aws_dynamodb_table_arns"] == []
    assert transformed["affected_aws_redshift_cluster_arns"] == []
