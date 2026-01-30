GET_RESOURCES_RESPONSE = [
    {
        "ResourceARN": "arn:aws:ec2:us-east-1:1234:instance/i-01",
        "Tags": [
            {
                "Key": "TestKey",
                "Value": "TestValue",
            },
        ],
    },
    {
        "ResourceARN": "arn:aws:s3:::bucket-1",
        "Tags": [
            {
                "Key": "Department",
                "Value": "Engineering",
            },
            {
                "Key": "Owner",
                "Value": "cartography",
            },
        ],
    },
    {
        "ResourceARN": "arn:aws:rds:us-east-1:1234:db:rds-db-1",
        "Tags": [
            {
                "Key": "Department",
                "Value": "Engineering",
            },
            {
                "Key": "LastReviewed",
                "Value": "January",
            },
        ],
    },
]

# a second response for a second instance we may use for testing
GET_RESOURCES_RESPONSE_UPDATED = [
    {
        "ResourceARN": "arn:aws:ec2:us-east-1:1234:instance/i-02",
        "Tags": [
            {
                "Key": "TestKeyUpdated",
                "Value": "TestValueUpdated",
            },
        ],
    },
]
