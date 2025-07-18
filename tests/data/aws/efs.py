import datetime

GET_EFS_FILE_SYSTEMS = [
    {
        "OwnerId": "123456789012",
        "CreationToken": "test-token-001",
        "FileSystemId": "fs-abc12345",
        "FileSystemArn": "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-abc12345",
        "CreationTime": datetime.datetime(
            2025,
            6,
            1,
        ),
        "LifeCycleState": "available",
        "Name": "TestFileSystem1",
        "NumberOfMountTargets": 1,
        "SizeInBytes": {
            "Value": 1048576,
            "Timestamp": datetime.datetime(
                2025,
                6,
                15,
            ),
        },
        "PerformanceMode": "generalPurpose",
        "Encrypted": True,
        "KmsKeyId": "arn:aws:kms:us-west-2:123456789012:key/abcde123-4567-8901-2345-abcdef123456",
        "ThroughputMode": "bursting",
        "AvailabilityZoneName": "us-west-2b",
        "AvailabilityZoneId": "usw2-az2",
        "FileSystemProtection": {"ReplicationOverwriteProtection": "ENABLED"},
    },
    {
        "OwnerId": "123456789012",
        "CreationToken": "test-token-002",
        "FileSystemId": "fs-def67890",
        "FileSystemArn": "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-def67890",
        "CreationTime": datetime.datetime(
            2025,
            6,
            5,
        ),
        "LifeCycleState": "updating",
        "Name": "TestFileSystem2",
        "NumberOfMountTargets": 1,
        "SizeInBytes": {
            "Value": 2097152,
            "Timestamp": datetime.datetime(
                2025,
                6,
                15,
            ),
        },
        "PerformanceMode": "maxIO",
        "Encrypted": False,
        "KmsKeyId": "",
        "ThroughputMode": "provisioned",
        "AvailabilityZoneName": "us-west-2b",
        "AvailabilityZoneId": "usw2-az2",
        "FileSystemProtection": {"ReplicationOverwriteProtection": "DISABLED"},
    },
]

GET_EFS_MOUNT_TARGETS = [
    {
        "OwnerId": "123456789012",
        "MountTargetId": "fsmt-9f8e7d6c5b4a3z2x",
        "FileSystemId": "fs-abc12345",
        "SubnetId": "subnet-9z8y7x6w",
        "LifeCycleState": "creating",
        "IpAddress": "192.168.1.20",
        "NetworkInterfaceId": "eni-789xyz123lmn456op",
        "AvailabilityZoneId": "usw2-az2",
        "AvailabilityZoneName": "us-west-2b",
        "VpcId": "vpc-1xyz234abc567defg",
    },
    {
        "OwnerId": "123456789012",
        "MountTargetId": "fsmt-abcdef1234567890",
        "FileSystemId": "fs-def67890",
        "SubnetId": "subnet-abcd1234",
        "LifeCycleState": "deleting",
        "IpAddress": "10.0.0.25",
        "NetworkInterfaceId": "eni-456abc789def123gh",
        "AvailabilityZoneId": "usw2-az2",
        "AvailabilityZoneName": "us-west-2b",
        "VpcId": "vpc-abc123def456ghi78",
    },
]


GET_EFS_ACCESS_POINTS = [
    {
        "ClientToken": "client-token-001",
        "Name": "AccessPoint1",
        "Tags": [
            {"Key": "Environment", "Value": "Dev"},
            {"Key": "Project", "Value": "TestProject1"},
        ],
        "AccessPointId": "fsap-111aaa222bbb333cc",
        "AccessPointArn": "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-111aaa222bbb333cc",
        "FileSystemId": "fs-abc12345",
        "PosixUser": {
            "Uid": 1001,
            "Gid": 1001,
            "SecondaryGids": [1002, 1003],
        },
        "RootDirectory": {
            "Path": "/app/data1",
            "CreationInfo": {"OwnerUid": 1001, "OwnerGid": 1001, "Permissions": "755"},
        },
        "OwnerId": "123456789012",
        "LifeCycleState": "available",
    },
    {
        "ClientToken": "client-token-002",
        "Name": "AccessPoint2",
        "Tags": [
            {"Key": "Environment", "Value": "Prod"},
            {"Key": "Project", "Value": "TestProject2"},
        ],
        "AccessPointId": "fsap-444ddd555eee666ff",
        "AccessPointArn": "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-444ddd555eee666ff",
        "FileSystemId": "fs-def67890",
        "PosixUser": {
            "Uid": 2001,
            "Gid": 2001,
            "SecondaryGids": [2002],
        },
        "RootDirectory": {
            "Path": "/app/data2",
            "CreationInfo": {"OwnerUid": 2001, "OwnerGid": 2001, "Permissions": "700"},
        },
        "OwnerId": "123456789012",
        "LifeCycleState": "updating",
    },
]
