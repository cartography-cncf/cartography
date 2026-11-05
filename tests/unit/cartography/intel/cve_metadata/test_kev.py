from datetime import datetime
from datetime import timezone

import pytest

from cartography.intel.cve_metadata.kev import transform_kev_catalog
from tests.data.cve_metadata.kev import GET_KEV_CATALOG


@pytest.mark.parametrize(
    "date_released",
    [
        "2024-01-10T15:00:00.0105Z",
        "2024-01-10T15:00:00.0105",
        "2024-01-10t15:00:00.0105z",
    ],
    ids=["utc", "no-offset-read-as-utc", "lowercase-rfc3339"],
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


# An unusable catalog must fail the fetch so that is_kev falls back to NVD. The
# catalog decides is_kev, so an empty or partial one would set the CVEs it leaves
# out to false.
@pytest.mark.parametrize(
    "overrides, error",
    [
        ({"vulnerabilities": []}, ValueError),
        ({"count": 3}, ValueError),
        ({"dateReleased": 0}, TypeError),
    ],
    ids=["no-entries", "count-mismatch", "non-string-date-released"],
)
def test_transform_unusable_kev_catalog_raises(overrides, error):
    # Act and assert
    with pytest.raises(error):
        transform_kev_catalog({**GET_KEV_CATALOG, **overrides})
