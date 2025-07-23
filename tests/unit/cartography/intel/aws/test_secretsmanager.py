import datetime
from datetime import timezone as tz

from cartography.intel.aws.secretsmanager import transform_secrets
from tests.data.aws.secretsmanager import SECRETS_RAW_DATA


def test_transform_secrets_happy_path():
    """Test that raw AWS API response data is correctly transformed."""
    # Arrange - verify input data is in raw format (datetime objects, nested RotationRules)
    assert isinstance(
        SECRETS_RAW_DATA[0]["CreatedDate"], datetime.datetime
    ), "Input should have datetime objects"
    assert (
        "AutomaticallyAfterDays" in SECRETS_RAW_DATA[0]["RotationRules"]
    ), "Input should have nested RotationRules"

    # Act
    transformed = transform_secrets(SECRETS_RAW_DATA)

    # Assert
    assert len(transformed) == 3, "Should transform all 3 secrets"

    # Test secret with rotation rules - verify transformation happened
    secret_with_rotation = transformed[0]

    # Verify datetime fields were converted to epoch integers
    assert isinstance(
        secret_with_rotation["CreatedDate"], int
    ), "CreatedDate should be converted from datetime to epoch int"
    assert isinstance(
        secret_with_rotation["LastRotatedDate"], int
    ), "LastRotatedDate should be converted to epoch int"
    assert isinstance(
        secret_with_rotation["LastChangedDate"], int
    ), "LastChangedDate should be converted to epoch int"
    assert isinstance(
        secret_with_rotation["LastAccessedDate"], int
    ), "LastAccessedDate should be converted to epoch int"

    # Verify specific epoch conversion (2024-01-15 10:30:00 UTC = 1705314600)
    expected_created_epoch = int(
        datetime.datetime(2024, 1, 15, 10, 30, 0, tzinfo=tz.utc).timestamp()
    )
    assert (
        secret_with_rotation["CreatedDate"] == expected_created_epoch
    ), "CreatedDate should be correctly converted to epoch"

    # Verify nested RotationRules.AutomaticallyAfterDays was flattened
    assert (
        secret_with_rotation["RotationRulesAutomaticallyAfterDays"] == 90
    ), "Should flatten RotationRules.AutomaticallyAfterDays"
    assert (
        "RotationRules" in secret_with_rotation
    ), "Original RotationRules should still exist"

    # Verify other fields pass through unchanged
    assert (
        secret_with_rotation["ARN"]
        == "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-with-rotation-AbCdEf"
    )
    assert secret_with_rotation["Name"] == "test-secret-with-rotation"
    assert secret_with_rotation["RotationEnabled"] is True
    assert secret_with_rotation["Description"] == "A test secret with rotation enabled"

    # Test secret without rotation rules - should not have flattened property
    secret_no_rotation = transformed[1]
    assert (
        "RotationRulesAutomaticallyAfterDays" not in secret_no_rotation
    ), "Should not add RotationRulesAutomaticallyAfterDays when RotationRules is missing"
    assert isinstance(
        secret_no_rotation["CreatedDate"], int
    ), "Date conversion should still happen"

    # Test minimal secret - verify graceful handling of missing fields
    minimal_secret = transformed[2]
    assert isinstance(
        minimal_secret["CreatedDate"], int
    ), "CreatedDate should be converted even in minimal data"
    assert (
        "RotationRulesAutomaticallyAfterDays" not in minimal_secret
    ), "Should not add missing properties"
    # Should handle None values gracefully for missing optional date fields
    assert minimal_secret.get("LastRotatedDate") is None or isinstance(
        minimal_secret.get("LastRotatedDate"), int
    )
