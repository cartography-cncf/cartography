TENANT_ID = "test-wiz-tenant"
GRAPHQL_URL = "https://api.us1.app.wiz.io/graphql"
AUTH_URL = "https://auth.app.wiz.io/oauth/token"
CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret"

RESOURCE_ID_1 = "wiz-resource-1"
RESOURCE_ID_2 = "wiz-resource-2"
ISSUE_ID_1 = "wiz-issue-1"
VULNERABILITY_ID_1 = "wiz-vuln-1"
CVE_ID_1 = "CVE-2024-12345"

RESOURCES = [
    {
        "id": RESOURCE_ID_1,
        "name": "prod-instance",
        "externalId": "arn:aws:ec2:us-east-1:123456789012:instance/i-123",
        "type": "VIRTUAL_MACHINE",
        "cloudPlatform": "AWS",
        "status": "ACTIVE",
        "region": "us-east-1",
        "tags": [{"key": "env", "value": "prod"}],
        "projects": [{"id": "project-1", "name": "Production"}],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "isOpenToAllInternet": False,
        "isAccessibleFromInternet": True,
        "hasAccessToSensitiveData": True,
        "hasAdminPrivileges": False,
        "hasHighPrivileges": True,
        "hasSensitiveData": True,
        "cloudAccount": {
            "id": "cloud-account-1",
            "name": "prod-aws",
            "cloudProvider": "AWS",
            "externalId": "123456789012",
        },
    },
    {
        "id": RESOURCE_ID_2,
        "name": "stale-instance",
        "externalId": "arn:aws:ec2:us-east-1:123456789012:instance/i-stale",
        "type": "VIRTUAL_MACHINE",
        "cloudPlatform": "AWS",
        "status": "ACTIVE",
        "projects": [{"id": "project-1", "name": "Production"}],
    },
]

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

VULNERABILITY_WITHOUT_ID = {
    "name": CVE_ID_1,
    "version": "1.0.0",
    "vulnerableAsset": {"id": RESOURCE_ID_1},
}
