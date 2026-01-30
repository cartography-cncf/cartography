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
        "VolumeId": "vol-0df",
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
        "VolumeId": "vol-03",
        "VolumeSize": 123,
        "OutpostArn": "arn1",
    },
]
