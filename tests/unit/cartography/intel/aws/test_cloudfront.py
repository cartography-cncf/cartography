from datetime import datetime
from datetime import timezone

from cartography.intel.aws.cloudfront import transform_distributions


def test_transform_distributions():
    # Arrange
    raw_dists = [
        {
            "Id": "E123",
            "LastModifiedTime": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]
    # Act
    dists = transform_distributions(raw_dists)
    # Assert
    assert dists[0]["LastModifiedTime"] == 1672574400
