TENANT_ID = "test-wiz-tenant"
GRAPHQL_URL = "https://api.us1.app.wiz.io/graphql"
AUTH_URL = "https://auth.app.wiz.io/oauth/token"
CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret"

RESOURCE_ID_1 = "wiz-resource-1"
ISSUE_ID_1 = "wiz-issue-1"
VULNERABILITY_ID_1 = "wiz-vuln-1"
NON_CVE_VULNERABILITY_ID = "wiz-vuln-no-cve-1"
CONFIGURATION_FINDING_ID_1 = "wiz-config-1"
DETECTION_ID_1 = "wiz-detection-1"
CVE_ID_1 = "CVE-2024-12345"

ISSUES = [
    {
        "id": ISSUE_ID_1,
        "createdAt": "2026-01-03T00:00:00Z",
        "updatedAt": "2026-01-04T00:00:00Z",
        "dueAt": "2026-01-10T00:00:00Z",
        "resolvedAt": None,
        "statusChangedAt": "2026-01-04T00:00:00Z",
        "status": "OPEN",
        "severity": "HIGH",
        "type": "CLOUD_CONFIGURATION",
        "control": {
            "id": "control-1",
            "name": "Public access",
            "description": "Resource is exposed",
            "resolutionRecommendation": "Restrict access",
        },
        "sourceRule": {"id": "rule-1", "name": "Public VM"},
        "project": {"id": "project-1", "name": "Production", "slug": "prod"},
        "entitySnapshot": {
            "id": RESOURCE_ID_1,
            "type": "VIRTUAL_MACHINE",
            "nativeType": "AWS::EC2::Instance",
            "name": "prod-instance",
            "status": "ACTIVE",
            "cloudPlatform": "AWS",
            "providerId": "i-123",
            "region": "us-east-1",
            "externalId": "arn:aws:ec2:us-east-1:123456789012:instance/i-123",
        },
        "serviceTickets": [
            {"externalId": "SEC-1", "name": "SEC-1", "url": "https://ticket/SEC-1"}
        ],
    },
]

VULNERABILITY_FINDINGS = [
    {
        "_wiz_finding_type": "VULNERABILITY",
        "id": VULNERABILITY_ID_1,
        "portalUrl": "https://app.wiz.io/vulnerability/wiz-vuln-1",
        "name": CVE_ID_1,
        "CVEDescription": "Test vulnerability",
        "CVSSSeverity": "HIGH",
        "score": 8.1,
        "exploitabilityScore": 2.8,
        "impactScore": 5.9,
        "hasExploit": True,
        "hasCisaKevExploit": False,
        "status": "OPEN",
        "vendorSeverity": "HIGH",
        "firstDetectedAt": "2026-01-05T00:00:00Z",
        "lastDetectedAt": "2026-01-06T00:00:00Z",
        "resolvedAt": None,
        "description": "Package is vulnerable",
        "remediation": "Upgrade package",
        "detailedName": "openssl",
        "version": "1.0.0",
        "fixedVersion": "1.0.1",
        "detectionMethod": "PACKAGE",
        "link": "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
        "locationPath": "/usr/lib/libssl.so",
        "resolutionReason": None,
        "vulnerableAsset": {
            "id": RESOURCE_ID_1,
            "type": "VIRTUAL_MACHINE",
            "name": "prod-instance",
            "region": "us-east-1",
            "providerUniqueId": "arn:aws:ec2:us-east-1:123456789012:instance/i-123",
            "cloudPlatform": "AWS",
            "status": "ACTIVE",
            "subscriptionName": "prod-aws",
            "subscriptionExternalId": "123456789012",
        },
    },
]

NON_CVE_VULNERABILITY_FINDINGS = [
    {
        **VULNERABILITY_FINDINGS[0],
        "id": NON_CVE_VULNERABILITY_ID,
        "portalUrl": "https://app.wiz.io/vulnerability/wiz-vuln-no-cve-1",
        "name": "openssl advisory",
        "CVEDescription": None,
        "CVSSSeverity": "MEDIUM",
        "score": 5.0,
        "exploitabilityScore": None,
        "impactScore": None,
        "hasExploit": False,
        "vendorSeverity": "MEDIUM",
        "firstDetectedAt": "2026-01-06T00:00:00Z",
        "description": "Vendor advisory without a CVE identifier",
        "link": None,
    },
]

VULNERABILITY_WITHOUT_ID = {
    "_wiz_finding_type": "VULNERABILITY",
    "name": CVE_ID_1,
    "version": "1.0.0",
    "vulnerableAsset": {"id": RESOURCE_ID_1},
}

CONFIGURATION_FINDINGS = [
    {
        "_wiz_finding_type": "CONFIGURATION",
        "id": CONFIGURATION_FINDING_ID_1,
        "targetExternalId": "arn:aws:s3:::public-bucket",
        "targetObjectProviderUniqueId": "s3/public-bucket",
        "firstSeenAt": "2026-01-07T00:00:00Z",
        "updatedAt": "2026-01-07T00:05:00Z",
        "severity": "CRITICAL",
        "result": "FAIL",
        "status": "OPEN",
        "remediation": "Disable public access",
        "resource": {
            "id": "wiz-resource-config-1",
            "providerId": "public-bucket",
            "name": "public-bucket",
            "nativeType": "AWS::S3::Bucket",
            "type": "BUCKET",
            "region": "us-east-1",
            "subscription": {
                "id": "cloud-account-1",
                "name": "prod-aws",
                "externalId": "123456789012",
                "cloudProvider": "AWS",
            },
            "projects": [{"id": "project-1", "name": "Production"}],
            "tags": [{"key": "env", "value": "prod"}],
        },
        "rule": {
            "id": "config-rule-1",
            "graphId": "graph-rule-1",
            "name": "S3 bucket is public",
            "description": "Bucket allows public access",
            "remediationInstructions": "Block public access",
            "functionAsControl": True,
        },
    },
]

DETECTIONS = [
    {
        "_wiz_finding_type": "DETECTION",
        "id": DETECTION_ID_1,
        "type": "MALWARE",
        "origins": ["WIZ_SENSOR"],
        "severity": "HIGH",
        "description": "Suspicious process detected",
        "createdAt": "2026-01-08T00:00:00Z",
        "updatedAt": "2026-01-08T00:05:00Z",
        "actors": [
            {
                "id": "actor-1",
                "name": "root",
                "externalId": "root",
                "providerUniqueId": "root",
                "type": "USER",
            }
        ],
        "resources": [
            {
                "id": "wiz-detection-resource-1",
                "name": "runtime-node",
                "externalId": "i-runtime",
                "providerUniqueId": "arn:aws:ec2:us-east-1:123456789012:instance/i-runtime",
                "type": "VIRTUAL_MACHINE",
            }
        ],
        "cloudAccounts": [
            {
                "id": "cloud-account-1",
                "name": "prod-aws",
                "externalId": "123456789012",
                "cloudProvider": "AWS",
            }
        ],
        "cloudOrganizations": [
            {
                "id": "cloud-org-1",
                "name": "prod-org",
                "externalId": "o-123",
                "cloudProvider": "AWS",
            }
        ],
        "primaryResource": {
            "id": "wiz-detection-resource-1",
            "type": "VIRTUAL_MACHINE",
            "name": "runtime-node",
            "externalId": "i-runtime",
            "region": "us-east-1",
        },
        "triggeringEvents": {
            "totalCount": 1,
            "nodes": [{"id": "event-1", "description": "Process started"}],
        },
        "ruleMatch": {
            "rule": {
                "id": "detect-rule-1",
                "name": "Suspicious process",
                "builtin": True,
            }
        },
    },
]

FINDINGS = (
    VULNERABILITY_FINDINGS
    + NON_CVE_VULNERABILITY_FINDINGS
    + CONFIGURATION_FINDINGS
    + DETECTIONS
)
