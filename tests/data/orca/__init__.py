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
ASSET_ID_1 = f"orca:{ORGANIZATION_ID}:{INVENTORY_ID_1}"
ASSET_ID_2 = f"orca:{ORGANIZATION_ID}:{INVENTORY_ID_2}"

ASSETS: list[dict[str, Any]] = [
    {
        "id": INVENTORY_ID_1,
        "type": "AwsEc2Instance",
        "name": "synthetic-app-server",
        "asset_unique_id": "asset-unique-1",
        "group_unique_id": "group-1",
        "cluster_unique_id": "cluster-1",
        "last_seen": "2026-08-13T12:00:00Z",
        "data": {
            "NewCategory": {"value": "Compute Services"},
            "NewSubCategory": {"value": "Virtual Instances"},
            "CloudProvider": {"value": "aws"},
            "CloudAccountId": {"value": "111122223333"},
            "Region": {"value": "us-west-2"},
            "Zones": {"value": ["us-west-2a"]},
            "UiUniqueField": {"value": "i-00000000000000001"},
            "Arn": {
                "value": "arn:aws:ec2:us-west-2:111122223333:instance/i-00000000000000001"
            },
            "State": {"value": "running"},
            "Exposure": {"value": "Internet facing"},
            "RiskLevel": {"value": "high"},
            "OrcaScore": {"value": 8.5},
            "ConsoleUrlLink": {"value": "https://app.example/assets/1"},
            "Tags": {"value": {"environment": "test", "owner": "security"}},
            "FirstSeen": {"value": "2026-08-01T12:00:00Z"},
            "CreationTime": {"value": "2026-07-01T12:00:00Z"},
        },
    },
    {
        "id": INVENTORY_ID_2,
        "type": "AzureStorageAccount",
        "name": "synthetic-storage",
        "asset_unique_id": "asset-unique-2",
        "group_unique_id": "group-2",
        "cluster_unique_id": "cluster-2",
        "last_seen": "2026-08-13T12:05:00Z",
        "data": {
            "NewCategory": {"value": "Data Storage"},
            "NewSubCategory": {"value": "Object Storage"},
            "CloudProvider": {"value": "azure"},
            "CloudAccountId": {"value": "subscription-1"},
            "Region": {"value": "westus2"},
            "UiUniqueField": {"value": "storage-account-1"},
            "RiskLevel": {"value": "low"},
            "OrcaScore": {"value": 2.1},
            "Tags": {"value": {}},
        },
    },
]

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
        "Inventory": {"id": INVENTORY_ID_1},
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
            "AssetUniqueId": "asset-unique-1",
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
