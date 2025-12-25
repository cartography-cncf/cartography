from datetime import datetime
from datetime import timezone

from cartography.intel.aws.athena import transform_work_groups
from cartography.intel.aws.glue import transform_glue_databases


def test_transform_work_groups():
    # Arrange
    raw_wgs = [
        {
            "Name": "primary",
            "CreationTime": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]
    # Act
    wgs = transform_work_groups(raw_wgs)
    # Assert
    assert wgs[0]["CreationTime"] == 1672574400


def test_transform_glue_databases():
    # Arrange
    raw_dbs = [
        {
            "Name": "db1",
            "CreateTime": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]
    # Act
    dbs = transform_glue_databases(raw_dbs, "us-east-1", "000000000000")
    # Assert
    assert dbs[0]["CreateTime"] == 1672574400
    assert dbs[0]["ARN"] == "arn:aws:glue:us-east-1:000000000000:database/db1"
