from datetime import datetime
from datetime import timezone

from cartography.intel.aws.cloudformation import transform_stacks


def test_transform_stacks():
    # Arrange
    raw_stacks = [
        {
            "StackId": "arn:aws:cloudformation:us-east-1:123:stack/test/123",
            "CreationTime": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "LastUpdatedTime": None,
        }
    ]
    # Act
    stacks = transform_stacks(raw_stacks)
    # Assert
    assert stacks[0]["CreationTime"] == 1672574400
    assert stacks[0]["LastUpdatedTime"] is None
