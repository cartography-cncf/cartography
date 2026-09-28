from typing import Any

API_ENDPOINT = "https://api.orcasecurity.example"
API_TOKEN = "synthetic-orca-token"
ORGANIZATION_ID = "orca-org-123"
ORGANIZATION: dict[str, Any] = {
    "id": ORGANIZATION_ID,
    "name": "Example Orca Organization",
    "api_url": API_ENDPOINT,
}

INVENTORY_ID_1 = "11111111-1111-4111-8111-111111111111"
INVENTORY_ID_2 = "22222222-2222-4222-8222-222222222222"
ASSET_UNIQUE_ID_1 = "asset-unique-1"
ASSET_UNIQUE_ID_2 = "asset-unique-2"
PROVIDER_ID_1 = "i-00000000000000001"
PROVIDER_ID_2 = "storage-account-1"
TARGET_ARN_1 = "arn:aws:ec2:us-west-2:111122223333:instance/i-00000000000000001"

ALERT_ID_1 = "orca-alert-1"
ALERT_ID_2 = "orca-alert-without-inventory"
ALERTS: list[dict[str, Any]] = [
    {
        "id": "alert-row-1",
        "data": {
            "AlertId": {"value": ALERT_ID_1},
            "Title": {"value": "Internet-facing compute asset"},
            "Details": {"value": "Synthetic alert details."},
            "Severity": {"value": "HIGH"},
            "Category": {"value": "Cloud Configuration"},
            "AlertType": {"value": "CONFIGURATION"},
            "OrcaScore": {"value": 8.5},
            "Status": {"value": "OPEN"},
            "CreatedAt": {"value": "2026-08-02T12:00:00Z"},
            "LastSeen": {"value": "2026-08-13T12:00:00Z"},
            "CveIds": {"value": ["CVE-2026-12345", "GHSA-not-a-cve"]},
            "AssetData": {
                "value": {
                    "asset_name": "synthetic-app-server",
                    "asset_type": "AwsEc2Instance",
                }
            },
        },
        "Inventory": {
            "id": INVENTORY_ID_1,
            "type": "AwsEc2Instance",
            "name": "synthetic-app-server",
            "asset_unique_id": ASSET_UNIQUE_ID_1,
            "data": {
                "UiUniqueField": {"value": PROVIDER_ID_1},
                "Arn": {"value": TARGET_ARN_1},
                "CloudProvider": {"value": "aws"},
                "CloudAccountId": {"value": "111122223333"},
                "Region": {"value": "us-west-2"},
            },
        },
    },
    {
        "id": "alert-row-2",
        "data": {
            "AlertId": {"value": ALERT_ID_2},
            "Title": {"value": "Deleted asset retained for investigation"},
            "Severity": {"value": "LOW"},
            "Category": {"value": "Data"},
            "AlertType": {"value": "DATA_AT_RISK"},
            "Status": {"value": "DISMISS"},
            "CreatedAt": {"value": "2026-08-03T12:00:00Z"},
            "AssetData": {
                "value": {
                    "asset_name": "removed-asset",
                    "asset_type": "Unknown",
                }
            },
        },
    },
]

CVE_ID_1 = "CVE-2026-12345"
VULNERABILITIES: list[dict[str, Any]] = [
    {
        "id": "vulnerability-row-1",
        "base_id_uuid": "vulnerability-base-1",
        "CveId": CVE_ID_1,
        "Description": "Synthetic package vulnerability.",
        "CvssScore": 9.8,
        "CvssSource": "NVD v3",
        "CvssSeverity": "CRITICAL",
        "CvssVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "EpssPercentile": 0.99,
        "EpssProbability": 0.75,
        "HasExploit": True,
        "CisaKev": True,
        "PatchAvailable": "Yes",
        "Trending": "No",
        "UpstreamDisposition": "affected",
        "SourceLink": "https://security.example/CVE-2026-12345",
        "FirstSeen": "2026-08-04T12:00:00Z",
        # Match Orca's public flat VulnerabilityV2 fixture: the related Inventory
        # carries base_id_uuid and AssetUniqueId, not its top-level Inventory.id.
        "Inventory": {
            "base_id_uuid": "related-inventory-base-uuid-not-top-level-id",
            "AssetUniqueId": ASSET_UNIQUE_ID_1,
            "UiUniqueField": PROVIDER_ID_1,
            "Arn": TARGET_ARN_1,
            "CloudProvider": "aws",
            "CloudAccountId": "111122223333",
            "Region": "us-west-2",
            "Name": "synthetic-app-server",
            "Type": "AwsEc2Instance",
        },
        "InstalledPackage": {
            # Orca's public fixture uses the graph-wide base UUID here rather
            # than an independently stable package identifier.
            "base_id_uuid": "vulnerability-base-1",
            "Name": "synthetic-lib",
            "Version": "1.0.0",
            "PURL": "pkg:deb/example/synthetic-lib@1.0.0",
            "CPE": "cpe:2.3:a:example:synthetic-lib:1.0.0:*:*:*:*:*:*:*",
            "SourcePackage": "synthetic-lib-source",
        },
    },
]
