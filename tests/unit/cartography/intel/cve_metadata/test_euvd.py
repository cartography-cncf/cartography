from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock

import pytest

from cartography.intel.cve_metadata import euvd
from tests.data.cve_metadata.euvd import EUVD_MENTIONING_RECORD
from tests.data.cve_metadata.euvd import EUVD_SEARCH_RESPONSES
from tests.data.cve_metadata.euvd import EUVD_UNSCORED_RECORD
from tests.data.cve_metadata.euvd import EUVD_V2_RECORD
from tests.data.cve_metadata.euvd import EUVD_V4_RECORD
from tests.data.cve_metadata.euvd import EUVD_XZ_RECORD


@pytest.mark.parametrize(
    "record, expected",
    [
        (
            EUVD_XZ_RECORD,
            {
                "euvd_id": "EUVD-2024-31700",
                "description_en": (
                    "Malicious code was discovered in the upstream tarballs of xz."
                ),
                "references_urls": [
                    "https://access.redhat.com/security/cve/CVE-2024-3094",
                    "https://www.openwall.com/lists/oss-security/2024/03/29/4",
                ],
                "published": datetime(2024, 3, 29, 16, 51, 12, tzinfo=timezone.utc),
                "cvss_version": "3.1",
                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                "baseScore": 10.0,
                "baseSeverity": "CRITICAL",
                "attackVector": "NETWORK",
                "attackComplexity": "LOW",
                "privilegesRequired": "NONE",
                "userInteraction": "NONE",
                "scope": "CHANGED",
                "confidentialityImpact": "HIGH",
                "integrityImpact": "HIGH",
                "availabilityImpact": "HIGH",
            },
        ),
        (
            EUVD_V4_RECORD,
            {
                "euvd_id": "EUVD-2026-118028",
                "description_en": "SQL injection in an example web application.",
                "references_urls": ["https://example.com/advisory"],
                "published": datetime(2026, 11, 6, 9, 30, 48, tzinfo=timezone.utc),
                "cvss_version": "4.0",
                "vectorString": (
                    "CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
                ),
                "baseScore": 8.7,
                "baseSeverity": "HIGH",
                "attackVector": "NETWORK",
                "attackComplexity": "LOW",
                "privilegesRequired": "LOW",
                "userInteraction": "NONE",
            },
        ),
        (
            EUVD_V2_RECORD,
            {
                "euvd_id": "EUVD-2013-0001",
                "description_en": "An old vulnerability scored only with CVSS 2.0.",
                "references_urls": [],
                "published": datetime(2013, 1, 2, 15, 4, 5, tzinfo=timezone.utc),
                "cvss_version": "2.0",
                "vectorString": "AV:N/AC:L/Au:N/C:C/I:P/A:N",
                "baseScore": 0.0,
                "baseSeverity": "LOW",
                "confidentialityImpact": "COMPLETE",
                "integrityImpact": "PARTIAL",
                "availabilityImpact": "NONE",
            },
        ),
        (
            EUVD_UNSCORED_RECORD,
            {
                "euvd_id": "EUVD-2026-00001",
                "description_en": "A vulnerability EUVD has not scored.",
                "references_urls": [],
                "published": datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
        ),
    ],
    ids=["cvss-3.1", "cvss-4.0-matches-nvd-fields", "cvss-2.0-zero-score", "unscored"],
)
def test_transform_euvd_record(record, expected):
    assert euvd.transform_euvd_record(record) == expected


def _search_session():
    def get(url, params, timeout):
        response = MagicMock()
        response.json.return_value = EUVD_SEARCH_RESPONSES[params["text"]]
        return response

    session = MagicMock()
    session.get.side_effect = get
    return session


def test_get_euvd_records_keeps_the_record_aliasing_the_cve():
    # Act
    records = euvd.get_euvd_records(
        _search_session(),
        ["CVE-2024-3094", "CVE-2026-0002"],
    )

    # Assert - the record that only mentions CVE-2024-3094 is skipped, and a CVE
    # EUVD does not know is left out.
    assert {cve_id: r["euvd_id"] for cve_id, r in records.items()} == {
        "CVE-2024-3094": "EUVD-2024-31700",
    }


def test_get_euvd_records_pages_until_the_alias_matches():
    # Arrange - the first page holds only records mentioning the CVE in their text.
    first_page = {
        "items": [
            {**EUVD_MENTIONING_RECORD, "id": f"EUVD-2024-{i:05d}"}
            for i in range(euvd.SEARCH_PAGE_SIZE)
        ],
        "total": euvd.SEARCH_PAGE_SIZE + 1,
    }
    pages = {"0": first_page, "1": {"items": [EUVD_XZ_RECORD], "total": 101}}

    def get(url, params, timeout):
        response = MagicMock()
        response.json.return_value = pages[params["page"]]
        return response

    session = MagicMock()
    session.get.side_effect = get

    # Act
    records = euvd.get_euvd_records(session, ["CVE-2024-3094"])

    # Assert
    assert records["CVE-2024-3094"]["euvd_id"] == "EUVD-2024-31700"


@pytest.mark.parametrize(
    "cve, expected",
    [
        ({"id": "CVE-1", "baseScore": 5.0}, False),
        ({"id": "CVE-1", "vulnStatus": "Rejected"}, False),
        ({"id": "CVE-1", "vulnStatus": "Awaiting Analysis"}, True),
        ({"id": "CVE-1"}, True),
    ],
    ids=["nvd-scored", "rejected", "awaiting-analysis", "not-in-nvd"],
)
def test_needs_euvd(cve, expected):
    assert euvd.needs_euvd(cve) is expected


def test_merge_euvd_fills_only_what_nvd_left_empty():
    # Arrange
    nvd_scored = {
        "id": "CVE-2024-3094",
        "description_en": "NVD's description.",
        "baseScore": 9.8,
        "cvss_source": "nvd",
    }
    unscored = {"id": "CVE-2026-123087", "vulnStatus": "Awaiting Analysis"}
    records = {
        "CVE-2024-3094": euvd.transform_euvd_record(EUVD_XZ_RECORD),
        "CVE-2026-123087": euvd.transform_euvd_record(EUVD_V4_RECORD),
    }

    # Act
    euvd.merge_euvd_into_cves([nvd_scored, unscored], records)

    # Assert
    assert nvd_scored["baseScore"] == 9.8
    assert nvd_scored["cvss_source"] == "nvd"
    assert nvd_scored["description_en"] == "NVD's description."
    assert nvd_scored["euvd_id"] == "EUVD-2024-31700"
    assert unscored == {
        "id": "CVE-2026-123087",
        "vulnStatus": "Awaiting Analysis",
        "euvd_id": "EUVD-2026-118028",
        "description_en": "SQL injection in an example web application.",
        "references_urls": ["https://example.com/advisory"],
        "published": datetime(2026, 11, 6, 9, 30, 48, tzinfo=timezone.utc),
        "cvss_version": "4.0",
        "vectorString": (
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
        ),
        "baseScore": 8.7,
        "baseSeverity": "HIGH",
        "attackVector": "NETWORK",
        "attackComplexity": "LOW",
        "privilegesRequired": "LOW",
        "userInteraction": "NONE",
        "cvss_source": "euvd",
    }
