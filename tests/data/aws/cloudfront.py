"""
Test data for AWS CloudFront intel module.

Data shapes based on real AWS CloudFront list_distributions API responses.
See: https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_ListDistributions.html
See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront/client/list_distributions.html
"""

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789

# Distribution with S3 origin
CLOUDFRONT_DISTRIBUTIONS = [
    {
        "Id": "E1A2B3C4D5E6F7",
        "ARN": f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E1A2B3C4D5E6F7",
        "ETag": "ABCDEF123456",
        "Status": "Deployed",
        "LastModifiedTime": "2025-01-01T12:00:00.000Z",
        "DomainName": "d1234567890abc.cloudfront.net",
        "Aliases": {
            "Quantity": 2,
            "Items": ["www.example.com", "example.com"],
        },
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "S3-my-bucket",
                    "DomainName": "my-test-bucket.s3.amazonaws.com",
                    "OriginPath": "",
                    "CustomHeaders": {"Quantity": 0},
                    "S3OriginConfig": {"OriginAccessIdentity": ""},
                    "ConnectionAttempts": 3,
                    "ConnectionTimeout": 10,
                    "OriginShield": {"Enabled": False},
                },
            ],
        },
        "OriginGroups": {"Quantity": 0},
        "DefaultCacheBehavior": {
            "TargetOriginId": "S3-my-bucket",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["HEAD", "GET"],
                "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
            },
            "SmoothStreaming": False,
            "Compress": True,
            "LambdaFunctionAssociations": {"Quantity": 0},
            "FunctionAssociations": {"Quantity": 0},
            "FieldLevelEncryptionId": "",
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        },
        "CacheBehaviors": {"Quantity": 0},
        "CustomErrorResponses": {"Quantity": 0},
        "Comment": "Test distribution with S3 origin",
        "PriceClass": "PriceClass_100",
        "Enabled": True,
        "ViewerCertificate": {
            "ACMCertificateArn": f"arn:aws:acm:us-east-1:{TEST_ACCOUNT_ID}:certificate/test-cert-1",
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021",
            "CloudFrontDefaultCertificate": False,
        },
        "Restrictions": {
            "GeoRestriction": {
                "RestrictionType": "whitelist",
                "Quantity": 2,
                "Items": ["US", "CA"],
            },
        },
        "WebACLId": "",
        "HttpVersion": "http2",
        "IsIPV6Enabled": True,
        "Staging": False,
    },
]

# Distribution with Lambda@Edge
CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA = [
    {
        "Id": "E7F8G9H0I1J2K3",
        "ARN": f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E7F8G9H0I1J2K3",
        "ETag": "GHIJKL789012",
        "Status": "Deployed",
        "LastModifiedTime": "2025-01-02T12:00:00.000Z",
        "DomainName": "d9876543210xyz.cloudfront.net",
        "Aliases": {
            "Quantity": 1,
            "Items": ["api.example.com"],
        },
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "S3-api-bucket",
                    "DomainName": "api-bucket.s3.us-east-1.amazonaws.com",
                    "OriginPath": "/api",
                    "CustomHeaders": {"Quantity": 0},
                    "S3OriginConfig": {"OriginAccessIdentity": ""},
                    "ConnectionAttempts": 3,
                    "ConnectionTimeout": 10,
                    "OriginShield": {"Enabled": False},
                },
            ],
        },
        "OriginGroups": {"Quantity": 0},
        "DefaultCacheBehavior": {
            "TargetOriginId": "S3-api-bucket",
            "ViewerProtocolPolicy": "https-only",
            "AllowedMethods": {
                "Quantity": 7,
                "Items": ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"],
                "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
            },
            "SmoothStreaming": False,
            "Compress": True,
            "LambdaFunctionAssociations": {
                "Quantity": 2,
                "Items": [
                    {
                        "LambdaFunctionARN": f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:auth-at-edge:1",
                        "EventType": "viewer-request",
                        "IncludeBody": False,
                    },
                    {
                        "LambdaFunctionARN": f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:response-headers:2",
                        "EventType": "origin-response",
                        "IncludeBody": False,
                    },
                ],
            },
            "FunctionAssociations": {"Quantity": 0},
            "FieldLevelEncryptionId": "",
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        },
        "CacheBehaviors": {"Quantity": 0},
        "CustomErrorResponses": {"Quantity": 0},
        "Comment": "API distribution with Lambda@Edge",
        "PriceClass": "PriceClass_All",
        "Enabled": True,
        "ViewerCertificate": {
            "ACMCertificateArn": f"arn:aws:acm:us-east-1:{TEST_ACCOUNT_ID}:certificate/test-cert-2",
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021",
            "CloudFrontDefaultCertificate": False,
        },
        "Restrictions": {
            "GeoRestriction": {
                "RestrictionType": "none",
                "Quantity": 0,
            },
        },
        "WebACLId": f"arn:aws:wafv2:us-east-1:{TEST_ACCOUNT_ID}:global/webacl/test-acl/abc123",
        "HttpVersion": "http2and3",
        "IsIPV6Enabled": True,
        "Staging": False,
    },
]

# Distribution with custom origin (not S3)
CLOUDFRONT_DISTRIBUTIONS_CUSTOM_ORIGIN = [
    {
        "Id": "E9Z8Y7X6W5V4U3",
        "ARN": f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E9Z8Y7X6W5V4U3",
        "ETag": "MNOPQR345678",
        "Status": "Deployed",
        "LastModifiedTime": "2025-01-03T12:00:00.000Z",
        "DomainName": "d5555555555555.cloudfront.net",
        "Aliases": {
            "Quantity": 0,
        },
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "Custom-origin",
                    "DomainName": "origin.backend.example.com",
                    "OriginPath": "",
                    "CustomHeaders": {"Quantity": 0},
                    "CustomOriginConfig": {
                        "HTTPPort": 80,
                        "HTTPSPort": 443,
                        "OriginProtocolPolicy": "https-only",
                        "OriginSslProtocols": {
                            "Quantity": 1,
                            "Items": ["TLSv1.2"],
                        },
                        "OriginReadTimeout": 30,
                        "OriginKeepaliveTimeout": 5,
                    },
                    "ConnectionAttempts": 3,
                    "ConnectionTimeout": 10,
                    "OriginShield": {
                        "Enabled": True,
                        "OriginShieldRegion": "us-east-1",
                    },
                },
            ],
        },
        "OriginGroups": {"Quantity": 0},
        "DefaultCacheBehavior": {
            "TargetOriginId": "Custom-origin",
            "ViewerProtocolPolicy": "allow-all",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["HEAD", "GET"],
                "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
            },
            "SmoothStreaming": False,
            "Compress": True,
            "LambdaFunctionAssociations": {"Quantity": 0},
            "FunctionAssociations": {"Quantity": 0},
            "FieldLevelEncryptionId": "",
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        },
        "CacheBehaviors": {"Quantity": 0},
        "CustomErrorResponses": {"Quantity": 0},
        "Comment": "Distribution with custom origin",
        "PriceClass": "PriceClass_200",
        "Enabled": True,
        "ViewerCertificate": {
            "CloudFrontDefaultCertificate": True,
            "MinimumProtocolVersion": "TLSv1",
        },
        "Restrictions": {
            "GeoRestriction": {
                "RestrictionType": "blacklist",
                "Quantity": 1,
                "Items": ["RU"],
            },
        },
        "WebACLId": "",
        "HttpVersion": "http2",
        "IsIPV6Enabled": False,
        "Staging": False,
    },
]

# Distribution with multiple S3 origins
CLOUDFRONT_DISTRIBUTIONS_MULTI_ORIGIN = [
    {
        "Id": "E3T2R1Q0P9O8N7",
        "ARN": f"arn:aws:cloudfront::{TEST_ACCOUNT_ID}:distribution/E3T2R1Q0P9O8N7",
        "ETag": "STUVWX901234",
        "Status": "Deployed",
        "LastModifiedTime": "2025-01-04T12:00:00.000Z",
        "DomainName": "d7777777777777.cloudfront.net",
        "Aliases": {
            "Quantity": 1,
            "Items": ["static.example.com"],
        },
        "Origins": {
            "Quantity": 2,
            "Items": [
                {
                    "Id": "S3-primary",
                    "DomainName": "primary-bucket.s3.amazonaws.com",
                    "OriginPath": "",
                    "CustomHeaders": {"Quantity": 0},
                    "S3OriginConfig": {"OriginAccessIdentity": ""},
                    "ConnectionAttempts": 3,
                    "ConnectionTimeout": 10,
                    "OriginShield": {"Enabled": False},
                },
                {
                    "Id": "S3-backup",
                    "DomainName": "backup-bucket.s3-website-us-west-2.amazonaws.com",
                    "OriginPath": "/backup",
                    "CustomHeaders": {"Quantity": 0},
                    "S3OriginConfig": {"OriginAccessIdentity": ""},
                    "ConnectionAttempts": 3,
                    "ConnectionTimeout": 10,
                    "OriginShield": {"Enabled": False},
                },
            ],
        },
        "OriginGroups": {"Quantity": 0},
        "DefaultCacheBehavior": {
            "TargetOriginId": "S3-primary",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["HEAD", "GET"],
                "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
            },
            "SmoothStreaming": False,
            "Compress": True,
            "LambdaFunctionAssociations": {"Quantity": 0},
            "FunctionAssociations": {"Quantity": 0},
            "FieldLevelEncryptionId": "",
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        },
        "CacheBehaviors": {
            "Quantity": 1,
            "Items": [
                {
                    "PathPattern": "/backup/*",
                    "TargetOriginId": "S3-backup",
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "AllowedMethods": {
                        "Quantity": 2,
                        "Items": ["HEAD", "GET"],
                        "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
                    },
                    "SmoothStreaming": False,
                    "Compress": True,
                    "LambdaFunctionAssociations": {
                        "Quantity": 1,
                        "Items": [
                            {
                                "LambdaFunctionARN": f"arn:aws:lambda:us-east-1:{TEST_ACCOUNT_ID}:function:backup-handler:1",
                                "EventType": "origin-request",
                                "IncludeBody": False,
                            },
                        ],
                    },
                    "FunctionAssociations": {"Quantity": 0},
                    "FieldLevelEncryptionId": "",
                    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
                },
            ],
        },
        "CustomErrorResponses": {"Quantity": 0},
        "Comment": "Distribution with multiple origins",
        "PriceClass": "PriceClass_100",
        "Enabled": True,
        "ViewerCertificate": {
            "ACMCertificateArn": f"arn:aws:acm:us-east-1:{TEST_ACCOUNT_ID}:certificate/test-cert-3",
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021",
            "CloudFrontDefaultCertificate": False,
        },
        "Restrictions": {
            "GeoRestriction": {
                "RestrictionType": "none",
                "Quantity": 0,
            },
        },
        "WebACLId": "",
        "HttpVersion": "http2",
        "IsIPV6Enabled": True,
        "Staging": False,
    },
]

# Simulated list_distributions API response
LIST_DISTRIBUTIONS_RESPONSE = {
    "DistributionList": {
        "Marker": "",
        "MaxItems": 100,
        "IsTruncated": False,
        "Quantity": 4,
        "Items": (
            CLOUDFRONT_DISTRIBUTIONS
            + CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA
            + CLOUDFRONT_DISTRIBUTIONS_CUSTOM_ORIGIN
            + CLOUDFRONT_DISTRIBUTIONS_MULTI_ORIGIN
        ),
    },
}

# Empty response
LIST_DISTRIBUTIONS_EMPTY_RESPONSE = {
    "DistributionList": {
        "Marker": "",
        "MaxItems": 100,
        "IsTruncated": False,
        "Quantity": 0,
    },
}
