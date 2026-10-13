from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.rds

TEST_REGION = "us-east-1"


@patch.object(cartography.intel.aws.rds, "aws_paginate")
@patch.object(cartography.intel.aws.rds, "create_boto3_client")
def test_get_rds_snapshot_data_only_checks_manual_snapshots(
    mock_create_client,
    mock_aws_paginate,
):
    client = MagicMock()
    mock_create_client.return_value = client
    mock_aws_paginate.return_value = [
        {
            "DBSnapshotIdentifier": "manual-snapshot",
            "SnapshotType": "manual",
        },
        {
            "DBSnapshotIdentifier": "automated-snapshot",
            "SnapshotType": "automated",
        },
    ]
    client.describe_db_snapshot_attributes.return_value = {
        "DBSnapshotAttributesResult": {
            "DBSnapshotAttributes": [
                {
                    "AttributeName": "restore",
                    "AttributeValues": ["all"],
                },
            ],
        },
    }

    snapshots = cartography.intel.aws.rds.get_rds_snapshot_data(
        MagicMock(),
        TEST_REGION,
    )

    assert snapshots[0]["Public"] is True
    assert snapshots[1]["Public"] is False
    client.describe_db_snapshot_attributes.assert_called_once_with(
        DBSnapshotIdentifier="manual-snapshot",
    )
