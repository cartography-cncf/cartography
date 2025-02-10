import datetime

DESCRIBE_SNAPSHOTS = [
    {
        "Description": "Snapshot for testing",
        "Encrypted": True,
        "OwnerId": "000000000000",
        "Progress": "56",
        "SnapshotId": "sn-01",
        "StartTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
        "State": "completed",
        "VolumeId": "v-01",
        "VolumeSize": 123,
        "OutpostArn": "arn1",
    },
    {
        "Description": "Snapshot for testing",
        "Encrypted": True,
        "OwnerId": "000000000000",
        "Progress": "56",
        "SnapshotId": "sn-02",
        "StartTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
        "State": "completed",
        "VolumeId": "v-02",
        "VolumeSize": 123,
        "OutpostArn": "arn1",
    },
]
