TEST_ACCOUNT_ID = "000000000000"
REGIONAL_WEB_ACL_ARN = (
    f"arn:aws:wafv2:us-west-2:{TEST_ACCOUNT_ID}:regional/webacl/regional-acl/acl-1"
)
CLOUDFRONT_WEB_ACL_ARN = (
    f"arn:aws:wafv2:us-east-1:{TEST_ACCOUNT_ID}:global/webacl/cloudfront-acl/acl-2"
)
LOAD_BALANCER_ARN = (
    f"arn:aws:elasticloadbalancing:us-west-2:{TEST_ACCOUNT_ID}:"
    "loadbalancer/app/example/abc123"
)
COGNITO_USER_POOL_ARN = (
    f"arn:aws:cognito-idp:us-west-2:{TEST_ACCOUNT_ID}:userpool/us-west-2_Example"
)

REGIONAL_WEB_ACLS = [
    {
        "Name": "regional-acl",
        "Id": "acl-1",
        "ARN": REGIONAL_WEB_ACL_ARN,
        "Description": "Protects regional applications",
        "DefaultAction": {"Allow": {}},
        "Capacity": 125,
        "ManagedByFirewallManager": False,
        "RetrofittedByFirewallManager": False,
        "LabelNamespace": f"awswaf:{TEST_ACCOUNT_ID}:webacl:regional-acl:",
        "VisibilityConfig": {
            "SampledRequestsEnabled": True,
            "CloudWatchMetricsEnabled": True,
            "MetricName": "regional-acl",
        },
        "Rules": [
            {
                "Name": "rate-limit-login",
                "Priority": 1,
                "Statement": {
                    "RateBasedStatement": {
                        "Limit": 100,
                        "AggregateKeyType": "IP",
                        "ScopeDownStatement": {
                            "IPSetReferenceStatement": {
                                "ARN": f"arn:aws:wafv2:us-west-2:{TEST_ACCOUNT_ID}:regional/ipset/office/ipset-1",
                            },
                        },
                    },
                },
                "Action": {"Block": {}},
                "VisibilityConfig": {
                    "SampledRequestsEnabled": True,
                    "CloudWatchMetricsEnabled": True,
                    "MetricName": "rate-limit-login",
                },
            },
        ],
    },
]

CLOUDFRONT_WEB_ACLS = [
    {
        "Name": "cloudfront-acl",
        "Id": "acl-2",
        "ARN": CLOUDFRONT_WEB_ACL_ARN,
        "DefaultAction": {"Block": {}},
        "Capacity": 700,
        "ManagedByFirewallManager": True,
        "VisibilityConfig": {
            "SampledRequestsEnabled": False,
            "CloudWatchMetricsEnabled": True,
            "MetricName": "cloudfront-acl",
        },
        "Rules": [
            {
                "Name": "aws-common-rules",
                "Priority": 10,
                "Statement": {
                    "ManagedRuleGroupStatement": {
                        "VendorName": "AWS",
                        "Name": "AWSManagedRulesCommonRuleSet",
                        "Version": "Version_1.0",
                    },
                },
                "OverrideAction": {"None": {}},
                "VisibilityConfig": {
                    "SampledRequestsEnabled": False,
                    "CloudWatchMetricsEnabled": True,
                    "MetricName": "aws-common-rules",
                },
            },
        ],
    },
]

LOGGING_CONFIGURATIONS = [
    {
        "ResourceArn": REGIONAL_WEB_ACL_ARN,
        "LogDestinationConfigs": [
            f"arn:aws:logs:us-west-2:{TEST_ACCOUNT_ID}:log-group:aws-waf-logs-main",
        ],
        "RedactedFields": [{"SingleHeader": {"Name": "authorization"}}],
        "LoggingFilter": {
            "DefaultBehavior": "KEEP",
            "Filters": [],
        },
    },
]

PROTECTED_RESOURCES = [
    {
        "ResourceType": "APPLICATION_LOAD_BALANCER",
        "ResourceArn": LOAD_BALANCER_ARN,
    },
    {
        "ResourceType": "COGNITO_USER_POOL",
        "ResourceArn": COGNITO_USER_POOL_ARN,
    },
]
