from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2

WAS_FINDING_ID_1 = "044a6c5f-3b1c-5c2d-bc76-36e0072ab19c"
WAS_FINDING_ID_2 = "155b7d6a-4c2d-6d3e-cd87-47f1183bc20d"

WAS_PLUGIN_ID_1 = 112435  # jQuery XSS — has CVEs
WAS_PLUGIN_ID_2 = 98765  # Generic info finding — no CVEs

WAS_SCAN_UUID_1 = "8c6490cf-7052-4167-bc9b-598edad80746"
WAS_SCAN_UUID_2 = "9d7501de-8163-5278-cd0c-609fbeae9185"

WAS_FINDINGS_DATA = [
    {
        # Medium-severity jQuery XSS on ASSET_ID_1, has CVEs
        "finding_id": WAS_FINDING_ID_1,
        "url": "https://www.unixtimestamp.com/contact.php",
        "output": "Current Version: 2.2.4\nFixed Version:   3.0.0\nDetected technology URL: https://www.unixtimestamp.com/contact.php",
        "state": "OPEN",
        "severity": "MEDIUM",
        "severity_id": 2,
        "severity_default_id": 2,
        "severity_modification_type": "NONE",
        "first_found": "2024-02-01T16:08:41Z",
        "last_found": "2024-02-01T16:08:41Z",
        "indexed_at": "2024-02-01T16:08:41Z",
        "plugin": {
            "id": WAS_PLUGIN_ID_1,
            "name": "jQuery 1.12.4 < 3.0.0 Cross-Site Scripting",
            "risk_factor": "MEDIUM",
            "type": "REMOTE",
            "synopsis": "jQuery 1.12.4 < 3.0.0 Cross-Site Scripting",
            "description": "According to its self-reported version number, jQuery is affected by a cross-site scripting vulnerability.",
            "solution": "Upgrade to jQuery version 3.0.0 or later.",
            "publication_date": "2018-11-05T00:00:00Z",
            "modification_date": "2023-03-14T00:00:00Z",
            "patch_publication_date": "2018-01-18T00:00:00Z",
            "exploitability_ease": "No known exploits are available",
            "in_the_news": False,
            "exploited_by_malware": False,
            "cvss2_base_score": 4.3,
            "cvss3_base_score": 6.1,
            "cvss4_base_score": 6.9,
            "vpr": {"score": 3},
            "vpr_v2": {"score": 4.9},
            "epss_score": 10.647,
            "cve": ["CVE-2015-9251"],
            "cwe": ["79"],
        },
        "asset": {
            "uuid": ASSET_ID_1,
            "fqdn": "www.unixtimestamp.com",
            "ipv4s": ["52.45.249.224"],
            "ipv4": "52.45.249.224",
        },
        "scan": {
            "uuid": WAS_SCAN_UUID_1,
            "completed_at": "2024-02-01T16:08:41Z",
        },
    },
    {
        # Info-severity finding on ASSET_ID_2, no CVEs
        "finding_id": WAS_FINDING_ID_2,
        "url": "https://example.com/api/health",
        "output": "Server header exposed: Apache/2.4.51",
        "state": "OPEN",
        "severity": "INFO",
        "severity_id": 0,
        "severity_default_id": 0,
        "severity_modification_type": "NONE",
        "first_found": "2024-03-10T09:00:00Z",
        "last_found": "2024-03-10T09:00:00Z",
        "indexed_at": "2024-03-10T09:00:00Z",
        "plugin": {
            "id": WAS_PLUGIN_ID_2,
            "name": "Web Server Version Disclosure",
            "risk_factor": "INFO",
            "type": "REMOTE",
            "synopsis": "The remote web server discloses its version.",
            "description": "The remote web server is disclosing its version in the Server HTTP response header.",
            "solution": "Configure the web server to suppress version information.",
            "publication_date": "2020-01-01T00:00:00Z",
            "modification_date": "2022-06-01T00:00:00Z",
            "patch_publication_date": None,
            "exploitability_ease": None,
            "in_the_news": False,
            "exploited_by_malware": False,
            "cvss2_base_score": None,
            "cvss3_base_score": None,
            "cvss4_base_score": None,
            "vpr": None,
            "vpr_v2": None,
            "epss_score": None,
            "cve": [],
            "cwe": [],
        },
        "asset": {
            "uuid": ASSET_ID_2,
            "fqdn": "example.com",
            "ipv4s": ["93.184.216.34"],
            "ipv4": "93.184.216.34",
        },
        "scan": {
            "uuid": WAS_SCAN_UUID_2,
            "completed_at": "2024-03-10T09:05:00Z",
        },
    },
]
