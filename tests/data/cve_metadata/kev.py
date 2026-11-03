# Shape of https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
# with entries trimmed to what the tests need. The flags are made up for the tests.
# CVE-2023-41782 is listed while the NVD fixture says it is not, and CVE-2024-22075
# is not listed while the NVD fixture says it is, so tests can tell which source won.
GET_KEV_CATALOG = {
    "title": "CISA Catalog of Known Exploited Vulnerabilities",
    "catalogVersion": "2024.01.10",
    "dateReleased": "2024-01-10T15:00:00.0105Z",
    "count": 2,
    "vulnerabilities": [
        {
            "cveID": "CVE-2023-41782",
            "vendorProject": "ZTE",
            "product": "ZXCLOUD iRAI",
            "vulnerabilityName": "ZTE ZXCLOUD iRAI DLL Hijacking Vulnerability",
            "dateAdded": "2024-01-09",
            "shortDescription": "Test entry.",
            "requiredAction": "Apply mitigations per vendor instructions.",
            "dueDate": "2024-01-30",
            "knownRansomwareCampaignUse": "Known",
            "forensicTriage": "Yes",
            "notes": "https://nvd.nist.gov/vuln/detail/CVE-2023-41782",
            "cwes": ["CWE-427"],
        },
        {
            "cveID": "CVE-2021-44228",
            "vendorProject": "Apache",
            "product": "Log4j2",
            "vulnerabilityName": "Apache Log4j2 Remote Code Execution Vulnerability",
            "dateAdded": "2021-12-10",
            "shortDescription": "Test entry.",
            "requiredAction": "Apply updates per vendor instructions.",
            "dueDate": "2021-12-24",
            "knownRansomwareCampaignUse": "Unknown",
            "forensicTriage": "No",
            "notes": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
            "cwes": ["CWE-20", "CWE-400", "CWE-502"],
        },
    ],
}
