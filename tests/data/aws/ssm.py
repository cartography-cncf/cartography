import datetime
from datetime import timezone as tz

INSTANCE_INFORMATION = [
    {
        "InstanceId": "i-01",
        "PingStatus": "Online",
        "LastPingDateTime": datetime.datetime(
            2022,
            3,
            14,
            4,
            56,
            22,
            962000,
            tzinfo=tz.utc,
        ),
        "AgentVersion": "3.1.1004.1",
        "IsLatestVersion": True,
        "PlatformType": "Linux",
        "PlatformName": "Amazon Linux",
        "PlatformVersion": "2",
        "ResourceType": "EC2Instance",
        "IPAddress": "10.0.0.1",
        "ComputerName": "ip-10-0-0-1.us-east-1.compute.internal",
        "AssociationStatus": "Pending",
        "LastAssociationExecutionDate": datetime.datetime(
            2022,
            3,
            14,
            4,
            58,
            28,
            395000,
            tzinfo=tz.utc,
        ),
        "LastSuccessfulAssociationExecutionDate": datetime.datetime(
            2022,
            3,
            14,
            4,
            28,
            28,
            395000,
            tzinfo=tz.utc,
        ),
        "AssociationOverview": {
            "DetailedStatus": "Pending",
            "InstanceAssociationStatusAggregatedCount": {
                "Pending": 1,
                "Success": 3,
            },
        },
        "SourceId": "i-01",
        "SourceType": "AWS::EC2::Instance",
    },
    {
        "InstanceId": "i-02",
        "PingStatus": "Online",
        "LastPingDateTime": datetime.datetime(
            2022,
            3,
            14,
            4,
            56,
            22,
            962000,
            tzinfo=tz.utc,
        ),
        "AgentVersion": "3.1.1004.0",
        "IsLatestVersion": False,
        "PlatformType": "Linux",
        "PlatformName": "Amazon Linux",
        "PlatformVersion": "2",
        "ResourceType": "EC2Instance",
        "IPAddress": "10.0.0.2",
        "ComputerName": "ip-10-0-0-2.us-east-1.compute.internal",
        "AssociationStatus": "Pending",
        "LastAssociationExecutionDate": datetime.datetime(
            2022,
            3,
            14,
            4,
            58,
            28,
            395000,
            tzinfo=tz.utc,
        ),
        "LastSuccessfulAssociationExecutionDate": datetime.datetime(
            2022,
            3,
            14,
            4,
            28,
            28,
            395000,
            tzinfo=tz.utc,
        ),
        "AssociationOverview": {
            "DetailedStatus": "Pending",
            "InstanceAssociationStatusAggregatedCount": {
                "Pending": 1,
                "Success": 3,
            },
        },
        "SourceId": "i-02",
        "SourceType": "AWS::EC2::Instance",
    },
]

INSTANCE_PATCHES = [
    {
        "Title": "test.x86_64:0:4.2.46-34.amzn2",
        "CVEIds": "CVE-2022-0000,CVE-2022-0001",
        "KBId": "test.x86_64",
        "Classification": "Security",
        "Severity": "Medium",
        "State": "Installed",
        "InstalledTime": datetime.datetime(2021, 11, 8, 20, 51, 18, tzinfo=tz.utc),
        "_instance_id": "i-01",
    },
    {
        "Title": "test.x86_64:0:4.2.46-34.amzn2",
        "CVEIds": "CVE-2022-0000,CVE-2022-0001",
        "KBId": "test.x86_64",
        "Classification": "Security",
        "Severity": "Medium",
        "State": "Installed",
        "InstalledTime": datetime.datetime(2021, 11, 8, 20, 51, 18, tzinfo=tz.utc),
        "_instance_id": "i-02",
    },
]


SSM_PARAMETERS_DATA = [
    {
        "Name": "/my/app/config/db-host",
        "ARN": "arn:aws:ssm:eu-west-1:000000000000:parameter/my/app/config/db-host",
        "Type": "SecureString",
        "KeyId": "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        "Version": 2,
        "LastModifiedDate": datetime.datetime(
            2023, 1, 15, 10, 0, 0, 123000, tzinfo=tz.utc
        ),
        "LastModifiedUser": "arn:aws:iam::000000000000:user/deploy-user",
        "Description": "Hostname for the primary application database.",
        "DataType": "text",
        "Tier": "Standard",
        "AllowedPattern": "^[a-zA-Z0-9.-]+$",
        "Policies": [
            {
                "PolicyText": '{"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": "*", "Action": "ssm:DeleteParameter", "Resource": "*"}]}',
                "PolicyType": "ResourceBased",
                "PolicyStatus": "Finished",
            },
        ],
    },
    {
        "Name": "/my/secure/api-key",
        "ARN": "arn:aws:ssm:eu-west-1:000000000000:parameter/my/secure/api-key",
        "Type": "SecureString",
        "KeyId": "arn:aws:kms:eu-west-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        "Version": 5,
        "LastModifiedDate": datetime.datetime(
            2023, 2, 20, 14, 30, 0, 456000, tzinfo=tz.utc
        ),
        "LastModifiedUser": "arn:aws:iam::000000000000:user/admin-user",
        "Description": "A super secret API key.",
        "DataType": "text",
        "Tier": "Advanced",
        "AllowedPattern": "^[a-zA-Z0-9]{32}$",
        "Policies": [
            {
                "PolicyText": '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "ssm:GetParameter", "Resource": "*"}]}',
                "PolicyType": "ResourceBased",
                "PolicyStatus": "Finished",
            },
        ],
    },
]
