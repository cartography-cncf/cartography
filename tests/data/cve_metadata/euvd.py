EUVD_XZ_RECORD = {
    "id": "EUVD-2024-31700",
    "enisaUuid": "c1dff3c6-59e6-308a-abce-02c029094ecd",
    "description": "Malicious code was discovered in the upstream tarballs of xz.",
    "datePublished": "Mar 29, 2024, 4:51:12 PM",
    "dateUpdated": "Nov 4, 2026, 9:11:43 PM",
    "baseScore": 10.0,
    "baseScoreVersion": "3.1",
    "baseScoreVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
    "references": (
        "https://access.redhat.com/security/cve/CVE-2024-3094\n"
        "https://www.openwall.com/lists/oss-security/2024/03/29/4\n"
    ),
    "aliases": "CVE-2024-3094\nGHSA-rxwq-x6h5-x525\n",
    "assigner": "redhat",
    "epss": 90.9,
    "enisaIdProduct": [],
    "enisaIdVendor": [],
}

EUVD_V4_RECORD = {
    "id": "EUVD-2026-118028",
    "description": "SQL injection in an example web application.",
    "datePublished": "Nov 6, 2026, 9:30:48 AM",
    "baseScore": 8.7,
    "baseScoreVersion": "4.0",
    "baseScoreVector": (
        "CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
    ),
    "references": "https://example.com/advisory\n",
    "aliases": "CVE-2026-123087\nGHSA-x2hr-mpw9-c694\n",
}

EUVD_UNSCORED_RECORD = {
    "id": "EUVD-2026-00001",
    "description": "A vulnerability EUVD has not scored.",
    "datePublished": "Nov 1, 2026, 12:00:00 AM",
    "baseScore": 0.0,
    "baseScoreVersion": None,
    "baseScoreVector": None,
    "references": "",
    "aliases": "CVE-2026-0001\n",
}

# A record that only mentions CVE-2024-3094 in its text, which EUVD's search also
# returns for that CVE.
EUVD_MENTIONING_RECORD = {
    "id": "EUVD-2024-99999",
    "description": "A follow-up to CVE-2024-3094 in another package.",
    "datePublished": "Apr 2, 2024, 10:00:00 AM",
    "baseScore": 5.5,
    "baseScoreVersion": "3.1",
    "baseScoreVector": "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
    "references": "",
    "aliases": "CVE-2024-99999\n",
}

EUVD_SEARCH_RESPONSES = {
    "CVE-2024-3094": {
        "items": [EUVD_MENTIONING_RECORD, EUVD_XZ_RECORD],
        "total": 2,
    },
    "CVE-2026-123087": {"items": [EUVD_V4_RECORD], "total": 1},
    "CVE-2026-0002": {"items": [], "total": 0},
}
