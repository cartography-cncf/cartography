from datetime import datetime
from datetime import timezone

TEST_ACCOUNTS = {
    "test-account-1": "111111111111",
    "test-account-2": "222222222222",
    "test-account-3": "444444444444",
}

TEST_ORGANIZATION = {
    "Id": "o-exampleorgid",
    "Arn": "arn:aws:organizations::111111111111:organization/o-exampleorgid",
    "FeatureSet": "ALL",
    "MasterAccountArn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
    "MasterAccountId": "111111111111",
    "MasterAccountEmail": "management@example.com",
    "AvailablePolicyTypes": [
        {
            "Type": "SERVICE_CONTROL_POLICY",
            "Status": "ENABLED",
        },
    ],
}

TEST_ORGANIZATION_ACCOUNTS = [
    {
        "Id": "111111111111",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
        "Email": "management@example.com",
        "Name": "management-account",
        "Status": "ACTIVE",
        "State": "ACTIVE",
        "JoinedMethod": "CREATED",
        "JoinedTimestamp": datetime(2020, 1, 1, tzinfo=timezone.utc),
    },
    {
        "Id": "222222222222",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/222222222222",
        "Email": "security@example.com",
        "Name": "security-account",
        "Status": "ACTIVE",
        "State": "ACTIVE",
        "JoinedMethod": "INVITED",
        "JoinedTimestamp": datetime(2020, 1, 2, tzinfo=timezone.utc),
    },
    {
        "Id": "333333333333",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/333333333333",
        "Email": "suspended@example.com",
        "Name": "suspended-account",
        "Status": "SUSPENDED",
        "State": "SUSPENDED",
        "JoinedMethod": "INVITED",
        "JoinedTimestamp": datetime(2020, 1, 3, tzinfo=timezone.utc),
    },
    {
        "Id": "444444444444",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/444444444444",
        "Email": "logging@example.com",
        "Name": "logging-account",
        "Status": "ACTIVE",
        "State": "ACTIVE",
        "JoinedMethod": "INVITED",
        "JoinedTimestamp": datetime(2020, 1, 4, tzinfo=timezone.utc),
    },
]

TEST_ORGANIZATION_ROOTS = [
    {
        "Id": "r-exam",
        "Arn": "arn:aws:organizations::111111111111:root/o-exampleorgid/r-exam",
        "Name": "Root",
        "PolicyTypes": [
            {
                "Type": "SERVICE_CONTROL_POLICY",
                "Status": "ENABLED",
            },
        ],
    },
]

TEST_ORGANIZATIONAL_UNITS = {
    "r-exam": [
        {
            "Id": "ou-exam-a1b2c3d4",
            "Arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-a1b2c3d4",
            "Name": "Security",
        },
    ],
    "ou-exam-a1b2c3d4": [
        {
            "Id": "ou-exam-b2c3d4e5",
            "Arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-b2c3d4e5",
            "Name": "Logging",
        },
    ],
    "ou-exam-b2c3d4e5": [],
}

TEST_ACCOUNTS_FOR_PARENT = {
    "r-exam": [
        TEST_ORGANIZATION_ACCOUNTS[0],
        TEST_ORGANIZATION_ACCOUNTS[2],
    ],
    "ou-exam-a1b2c3d4": [
        TEST_ORGANIZATION_ACCOUNTS[1],
    ],
    "ou-exam-b2c3d4e5": [
        TEST_ORGANIZATION_ACCOUNTS[3],
    ],
}

TEST_SERVICE_CONTROL_POLICIES = [
    {
        "Id": "p-FullAWSAccess",
        "Arn": "arn:aws:organizations::aws:policy/service_control_policy/p-FullAWSAccess",
        "Name": "FullAWSAccess",
        "Description": "Allows access to every operation",
        "Type": "SERVICE_CONTROL_POLICY",
        "AwsManaged": True,
        "Content": '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}',
        "Targets": [
            {
                "TargetId": "r-exam",
                "Arn": "arn:aws:organizations::111111111111:root/o-exampleorgid/r-exam",
                "Name": "Root",
                "Type": "ROOT",
            },
            {
                "TargetId": "ou-exam-a1b2c3d4",
                "Arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-a1b2c3d4",
                "Name": "Security",
                "Type": "ORGANIZATIONAL_UNIT",
            },
            {
                "TargetId": "111111111111",
                "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
                "Name": "management-account",
                "Type": "ACCOUNT",
            },
        ],
    },
    {
        "Id": "p-examregion",
        "Arn": "arn:aws:organizations::111111111111:policy/o-exampleorgid/service_control_policy/p-examregion",
        "Name": "DenyUnapprovedRegions",
        "Description": "Deny requests outside approved regions",
        "Type": "SERVICE_CONTROL_POLICY",
        "AwsManaged": False,
        "Content": (
            '{"Version":"2012-10-17","Statement":[{"Sid":"DenyOutsideApprovedRegions",'
            '"Effect":"Deny","NotAction":["iam:*","organizations:*","sts:*"],"Resource":"*",'
            '"Condition":{"StringNotEquals":{"aws:RequestedRegion":["us-east-1","us-west-2"]}}}]}'
        ),
        "Targets": [
            {
                "TargetId": "ou-exam-a1b2c3d4",
                "Arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-a1b2c3d4",
                "Name": "Security",
                "Type": "ORGANIZATIONAL_UNIT",
            },
            {
                "TargetId": "444444444444",
                "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/444444444444",
                "Name": "logging-account",
                "Type": "ACCOUNT",
            },
        ],
    },
]
