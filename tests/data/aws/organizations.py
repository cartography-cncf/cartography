TEST_ACCOUNTS = {
    "test-account-1": "111111111111",
    "test-account-2": "222222222222",
}

TEST_ORGANIZATION = {
    "Id": "o-exampleorgid",
    "Arn": "arn:aws:organizations::111111111111:organization/o-exampleorgid",
    "FeatureSet": "ALL",
    "MasterAccountArn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
    "MasterAccountId": "111111111111",
    "MasterAccountEmail": "management@example.com",
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
        "JoinedTimestamp": "2020-01-01T00:00:00Z",
    },
    {
        "Id": "222222222222",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/222222222222",
        "Email": "security@example.com",
        "Name": "security-account",
        "Status": "ACTIVE",
        "State": "ACTIVE",
        "JoinedMethod": "INVITED",
        "JoinedTimestamp": "2020-01-02T00:00:00Z",
    },
    {
        "Id": "333333333333",
        "Arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/333333333333",
        "Email": "suspended@example.com",
        "Name": "suspended-account",
        "Status": "ACTIVE",
        "State": "SUSPENDED",
        "JoinedMethod": "INVITED",
        "JoinedTimestamp": "2020-01-03T00:00:00Z",
    },
]
