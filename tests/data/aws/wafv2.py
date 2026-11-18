"""
WAFv2 API responses, shaped like the boto3 wafv2 client returns them.

The protected resource ARNs below are the ones the other AWS fixtures load, so
integration tests can seed those resources with the real Cartography loaders.
"""

TEST_ACCOUNT_ID = "000000000000"

# The application load balancer in
# tests.data.aws.ec2.load_balancer_v2s.GET_LOAD_BALANCER_V2_DATA.
PROTECTED_ALB_ARN = (
    "arn:aws:elasticloadbalancing:us-east-1:000000000000:"
    "loadbalancer/app/test-alb/1234567890123456"
)

ALB_WEB_ACL_ARN = (
    "arn:aws:wafv2:us-east-1:000000000000:regional/webacl/"
    "alb-acl/11111111-1111-1111-1111-111111111111"
)
# The webAclArn of both stages in tests.data.aws.apigateway.GET_STAGES.
API_GATEWAY_WEB_ACL_ARN = (
    "arn:aws:wafv2:us-west-2:1234567890:regional/webacl/"
    "test-cli/a1b2c3d4-5678-90ab-cdef-EXAMPLE111"
)
# The WebACLId of the distribution in
# tests.data.aws.cloudfront.CLOUDFRONT_DISTRIBUTIONS_WITH_LAMBDA.
CLOUDFRONT_WEB_ACL_ARN = (
    "arn:aws:wafv2:us-east-1:000000000000:global/webacl/test-acl/abc123"
)
GOVCLOUD_WEB_ACL_ARN = (
    "arn:aws-us-gov:wafv2:us-gov-west-1:000000000000:regional/webacl/"
    "gov-acl/44444444-4444-4444-4444-444444444444"
)

ALB_WEB_ACL_SUMMARY = {
    "Name": "alb-acl",
    "Id": "11111111-1111-1111-1111-111111111111",
    "Description": "Protects the public load balancer",
    "LockToken": "lock-token-1",
    "ARN": ALB_WEB_ACL_ARN,
}
API_GATEWAY_WEB_ACL_SUMMARY = {
    "Name": "test-cli",
    "Id": "a1b2c3d4-5678-90ab-cdef-EXAMPLE111",
    "Description": "",
    "LockToken": "lock-token-2",
    "ARN": API_GATEWAY_WEB_ACL_ARN,
}
CLOUDFRONT_WEB_ACL_SUMMARY = {
    "Name": "test-acl",
    "Id": "abc123",
    "Description": "Protects the CDN",
    "LockToken": "lock-token-3",
    "ARN": CLOUDFRONT_WEB_ACL_ARN,
}
GOVCLOUD_WEB_ACL_SUMMARY = {
    "Name": "gov-acl",
    "Id": "44444444-4444-4444-4444-444444444444",
    "Description": "",
    "LockToken": "lock-token-4",
    "ARN": GOVCLOUD_WEB_ACL_ARN,
}

# list_web_acls(Scope="REGIONAL") in us-east-1.
LIST_WEB_ACLS_REGIONAL_US_EAST_1 = {"WebACLs": [ALB_WEB_ACL_SUMMARY]}
# list_web_acls(Scope="REGIONAL") in us-west-2.
LIST_WEB_ACLS_REGIONAL_US_WEST_2 = {"WebACLs": [API_GATEWAY_WEB_ACL_SUMMARY]}
# list_web_acls(Scope="CLOUDFRONT"), which AWS only serves from us-east-1.
LIST_WEB_ACLS_CLOUDFRONT = {"WebACLs": [CLOUDFRONT_WEB_ACL_SUMMARY]}
# list_web_acls(Scope="REGIONAL") in us-gov-west-1.
LIST_WEB_ACLS_REGIONAL_US_GOV_WEST_1 = {"WebACLs": [GOVCLOUD_WEB_ACL_SUMMARY]}

# list_resources_for_web_acl(ResourceType="APPLICATION_LOAD_BALANCER").
LIST_RESOURCES_FOR_ALB_WEB_ACL = {"ResourceArns": [PROTECTED_ALB_ARN]}
LIST_RESOURCES_NONE: dict[str, list[str]] = {"ResourceArns": []}

# Two list_web_acls pages. WAF returns a NextMarker whenever it fills a page,
# so the last page can carry one too; the call after it returns no web ACLs.
LIST_WEB_ACLS_FIRST_PAGE = {
    "WebACLs": [ALB_WEB_ACL_SUMMARY],
    "NextMarker": "alb-acl",
}
LIST_WEB_ACLS_LAST_PAGE = {
    "WebACLs": [API_GATEWAY_WEB_ACL_SUMMARY],
    "NextMarker": "test-cli",
}
LIST_WEB_ACLS_EMPTY_PAGE_WITH_MARKER = {
    "WebACLs": [],
    "NextMarker": "test-cli",
}
