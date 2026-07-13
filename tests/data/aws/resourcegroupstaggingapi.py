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

# Two classic load balancers with the SAME name in two different regions. The
# classic LB tag mapping is keyed by the non-unique `name` property, so without
# a region predicate the tagging API would cross-tag both LBs (issue #1137).
SAME_NAME_LB = "my-lb"

LOAD_BALANCERS_US_EAST_1 = [
    {
        "id": f"{SAME_NAME_LB}-us-east-1.elb.amazonaws.com",
        "name": SAME_NAME_LB,
        "dnsname": f"{SAME_NAME_LB}-us-east-1.elb.amazonaws.com",
    },
]

LOAD_BALANCERS_US_WEST_2 = [
    {
        "id": f"{SAME_NAME_LB}-us-west-2.elb.amazonaws.com",
        "name": SAME_NAME_LB,
        "dnsname": f"{SAME_NAME_LB}-us-west-2.elb.amazonaws.com",
    },
]

# Tagging API responses: the us-east-1 LB is tagged env:prod, the same-named
# us-west-2 LB is tagged env:staging.
GET_RESOURCES_RESPONSE_LB_US_EAST_1 = [
    {
        "ResourceARN": f"arn:aws:elasticloadbalancing:us-east-1:1234:loadbalancer/{SAME_NAME_LB}",
        "Tags": [
            {
                "Key": "env",
                "Value": "prod",
            },
        ],
    },
]

GET_RESOURCES_RESPONSE_LB_US_WEST_2 = [
    {
        "ResourceARN": f"arn:aws:elasticloadbalancing:us-west-2:1234:loadbalancer/{SAME_NAME_LB}",
        "Tags": [
            {
                "Key": "env",
                "Value": "staging",
            },
        ],
    },
]
