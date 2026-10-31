import datetime

TEST_SHARE_ARN = (
    "arn:aws:ram:eu-west-1:000000000000:resource-share/"
    "11111111-2222-3333-4444-555555555555"
)
TEST_TGW_ARN = (
    "arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0"
)

GET_RAM_RESOURCE_SHARES = [
    {
        "resourceShareArn": TEST_SHARE_ARN,
        "name": "shared-transit-gateway",
        "owningAccountId": "000000000000",
        "allowExternalPrincipals": True,
        "status": "ACTIVE",
        "creationTime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "lastUpdatedTime": datetime.datetime(2024, 1, 2, 0, 0, 0),
        "featureSet": "STANDARD",
    },
]

GET_RAM_PRINCIPALS = [
    # An account inside the organization.
    {
        "id": "000000000001",
        "resourceShareArn": TEST_SHARE_ARN,
        "creationTime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "lastUpdatedTime": datetime.datetime(2024, 1, 2, 0, 0, 0),
        "external": False,
    },
    # An account outside the organization: has no AWSAccount node of its own.
    {
        "id": "999999999999",
        "resourceShareArn": TEST_SHARE_ARN,
        "creationTime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "lastUpdatedTime": datetime.datetime(2024, 1, 2, 0, 0, 0),
        "external": True,
    },
    # A non-account principal: an organizational unit ARN, which matches no AWSAccount.
    {
        "id": "arn:aws:organizations::000000000000:ou/o-abcd1234/ou-abcd-12345678",
        "resourceShareArn": TEST_SHARE_ARN,
        "creationTime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "lastUpdatedTime": datetime.datetime(2024, 1, 2, 0, 0, 0),
        "external": False,
    },
]

GET_RAM_RESOURCES = [
    {
        "arn": TEST_TGW_ARN,
        "type": "ec2:TransitGateway",
        "resourceShareArn": TEST_SHARE_ARN,
        "status": "AVAILABLE",
        "creationTime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "lastUpdatedTime": datetime.datetime(2024, 1, 2, 0, 0, 0),
    },
]
