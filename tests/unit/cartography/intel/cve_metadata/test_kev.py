from datetime import datetime
from datetime import timezone

import pytest

from cartography.intel.cve_metadata.kev import merge_kev_into_cves
from cartography.intel.cve_metadata.kev import transform_kev_catalog
from tests.data.cve_metadata.kev import GET_KEV_CATALOG


@pytest.mark.parametrize(
    "date_released",
    ["2024-01-10T15:00:00.0105Z", "2024-01-10T15:00:00.0105"],
    ids=["utc", "no-offset-read-as-utc"],
)
def test_transform_kev_catalog(date_released):
    # Act
    catalog = transform_kev_catalog({**GET_KEV_CATALOG, "dateReleased": date_released})

    # Assert
    assert catalog.catalog_version == "2024.01.10"
    assert catalog.date_released == datetime(
        2024, 1, 10, 15, 0, 0, 10500, tzinfo=timezone.utc
    )
    assert catalog.entries == {
        "CVE-2023-41782": {
            "kev_date_added": "2024-01-09",
            "kev_due_date": "2024-01-30",
            "kev_ransomware_use": "Known",
            "kev_forensic_triage": True,
        },
        "CVE-2021-44228": {
            "kev_date_added": "2021-12-10",
            "kev_due_date": "2021-12-24",
            "kev_ransomware_use": "Unknown",
            "kev_forensic_triage": False,
        },
    }


def test_transform_kev_catalog_without_entries_raises():
    # An empty catalog would otherwise set every is_kev to false.
    with pytest.raises(ValueError):
        transform_kev_catalog({**GET_KEV_CATALOG, "vulnerabilities": []})


def test_merge_kev_catalog_overrides_nvd():
    # Arrange: NVD's copy disagrees with the catalog on both CVEs.
    catalog = transform_kev_catalog(GET_KEV_CATALOG)
    cves = [
        {"id": "CVE-2023-41782", "is_kev": False},
        {"id": "CVE-2024-22075", "is_kev": True, "cisaExploitAdd": "2024-01-08"},
    ]

    # Act
    merge_kev_into_cves(cves, catalog)

    # Assert
    assert cves == [
        {
            "id": "CVE-2023-41782",
            "is_kev": True,
            "is_kev_source": "kev",
            "kev_date_added": "2024-01-09",
            "kev_due_date": "2024-01-30",
            "kev_ransomware_use": "Known",
            "kev_forensic_triage": True,
        },
        {
            "id": "CVE-2024-22075",
            "is_kev": False,
            "is_kev_source": "kev",
            "cisaExploitAdd": "2024-01-08",
            "kev_date_added": None,
            "kev_due_date": None,
            "kev_ransomware_use": None,
            "kev_forensic_triage": None,
        },
    ]


def test_merge_kev_without_catalog_falls_back_to_nvd():
    # Arrange: the second CVE has no NVD record.
    cves = [{"id": "CVE-2024-22075", "is_kev": True}, {"id": "CVE-2023-41782"}]

    # Act
    merge_kev_into_cves(cves, None)

    # Assert
    assert [(c["id"], c.get("is_kev"), c["is_kev_source"]) for c in cves] == [
        ("CVE-2024-22075", True, "nvd"),
        ("CVE-2023-41782", None, None),
    ]
    assert all(c["kev_date_added"] is None for c in cves)
