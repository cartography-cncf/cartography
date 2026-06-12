TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"

REGIONAL_WEB_ACL_ARN = (
    f"arn:aws:wafv2:{TEST_REGION}:{TEST_ACCOUNT_ID}:regional/webacl/"
    "regional-acl/11111111-1111-1111-1111-111111111111"
)
CLOUDFRONT_WEB_ACL_ARN = (
    f"arn:aws:wafv2:us-east-1:{TEST_ACCOUNT_ID}:global/webacl/"
    "cloudfront-acl/22222222-2222-2222-2222-222222222222"
)
PROTECTED_ALB_ARN = (
    f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_ACCOUNT_ID}:"
    "loadbalancer/app/my-alb/1234567890abcdef"
)

GET_WEB_ACLS_REGIONAL = [
    {
        "Name": "regional-acl",
        "Id": "11111111-1111-1111-1111-111111111111",
        "Description": "Protects the regional API",
        "LockToken": "lock-token-1",
        "ARN": REGIONAL_WEB_ACL_ARN,
        "AlbArns": [PROTECTED_ALB_ARN],
    },
]

GET_WEB_ACLS_CLOUDFRONT = [
    {
        "Name": "cloudfront-acl",
        "Id": "22222222-2222-2222-2222-222222222222",
        "Description": "Protects the CDN",
        "LockToken": "lock-token-2",
        "ARN": CLOUDFRONT_WEB_ACL_ARN,
    },
]

LIST_WEB_ACLS_PAGES = [
    {
        "WebACLs": [
            {
                "Name": "regional-acl",
                "Id": "11111111-1111-1111-1111-111111111111",
                "Description": "Protects the regional API",
                "LockToken": "lock-token-1",
                "ARN": REGIONAL_WEB_ACL_ARN,
            },
        ],
        "NextMarker": "regional-acl",
    },
    {
        "WebACLs": [
            {
                "Name": "regional-acl-2",
                "Id": "33333333-3333-3333-3333-333333333333",
                "Description": "",
                "LockToken": "lock-token-3",
                "ARN": (
                    f"arn:aws:wafv2:{TEST_REGION}:{TEST_ACCOUNT_ID}:regional/webacl/"
                    "regional-acl-2/33333333-3333-3333-3333-333333333333"
                ),
            },
        ],
    },
]

LIST_RESOURCES_FOR_WEB_ACL = {
    "ResourceArns": [PROTECTED_ALB_ARN],
}
