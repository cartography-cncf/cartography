TENANT_ID = "example-tenant"
API_KEY = "00000000-0000-0000-0000-000000000001"
API_SECRET = "00000000-0000-0000-0000-000000000002"

ACCOUNT_ID = "123456789012"
ORG_MANAGEMENT_ACCOUNT_ID = "210987654321"

IMAGE_DIGEST = "sha256:" + "a" * 64

CVE_VULNERABILITY_ID = "vuln-instance-1"
GHSA_VULNERABILITY_ID = "vuln-instance-2"
CVE_ID = "CVE-2024-3094"
GHSA_ID = "GHSA-xxxx-yyyy-zzzz"

ATTACK_CHAIN_ID = "chain-1"
ATTACK_CHAIN_DOMAIN = "api.example.com"

AWS_ACCOUNTS = [
    {
        "accountId": ACCOUNT_ID,
        "roleArn": f"arn:aws:iam::{ACCOUNT_ID}:role/SweetSecurityRole",
        "regions": ["us-east-1", "us-west-2"],
        "externalId": "example-external-id",
        "enabled": True,
    },
]

AWS_ORGANIZATIONS = [
    {
        "accountId": ORG_MANAGEMENT_ACCOUNT_ID,
        "roleArn": f"arn:aws:iam::{ORG_MANAGEMENT_ACCOUNT_ID}:role/SweetSecurityRole",
        "roleNameParameterArn": (
            f"arn:aws:ssm:us-east-1:{ORG_MANAGEMENT_ACCOUNT_ID}:parameter/sweet-role"
        ),
        "regions": ["us-east-1"],
        "externalId": "example-external-id",
        "enabled": True,
    },
]

VULNERABILITIES = [
    {
        "id": CVE_VULNERABILITY_ID,
        "cve": CVE_ID,
        "severity": "critical",
        "status": "Open",
        "sweetScore": 9.1,
        "sweetSeverity": "critical",
        "epssScore": 0.85,
        "epssPercentile": 98.7,
        "riskIndicators": ["internet_facing", "loaded_in_memory"],
        "attackLabels": ["remote_code_execution"],
        "publishedDate": "2024-03-29T17:15:00Z",
        "firstDetected": "2026-10-01T00:00:00Z",
        "lastDetected": "2026-11-15T00:00:00Z",
        "lastExecuted": None,
        "lastLoaded": "2026-11-14T12:00:00Z",
        "hasFix": True,
        "fixedInVersions": ["5.6.1"],
        "codeOwner": {"name": "Example Team", "email": "team@example.com"},
        "package": {"name": "xz-utils", "version": "5.6.0", "manager": "deb"},
        "image": {
            "name": "example/api",
            "tag": "1.2.3",
            "digest": IMAGE_DIGEST,
            "registry": f"{ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com",
        },
        "workload": "api",
        "cloudAccount": "example-production",
    },
    {
        "id": GHSA_VULNERABILITY_ID,
        "cve": GHSA_ID,
        "severity": "medium",
        "status": "Ignored",
        "sweetScore": None,
        "sweetSeverity": None,
        "epssScore": None,
        "epssPercentile": None,
        "riskIndicators": [],
        "attackLabels": [],
        "publishedDate": None,
        "firstDetected": "2026-10-02T00:00:00Z",
        "lastDetected": "2026-11-15T00:00:00Z",
        "lastExecuted": None,
        "lastLoaded": None,
        "hasFix": False,
        "fixedInVersions": [],
        "codeOwner": None,
        "package": {"name": "example-lib", "version": "0.1.0", "manager": "npm"},
        "image": None,
        "workload": "worker",
        "cloudAccount": "example-production",
    },
]

ATTACK_CHAINS = [
    {
        "id": ATTACK_CHAIN_ID,
        "title": "Unauthenticated access to order history",
        "description": "An unauthenticated caller can read other users' orders.",
        "story": "1. **Recon** found endpoint\n2. **Exploit** read another user's order",
        "severity": "high",
        "status": "Open",
        "confidence": "fully-validated",
        "impact": ["data_exposure"],
        "owasp": ["API1:2023"],
        "domain": "API.Example.com.",
        "endpoints": [
            {"method": "GET", "path": "/v1/orders/{id}"},
        ],
        "firstDetectedAt": "2026-11-10T00:00:00Z",
        "lastDetectedAt": "2026-11-15T00:00:00Z",
        "executionName": "",
        "campaignName": "",
        "assetId": None,
        "cwe": ["CWE-639"],
    },
]
