import io
from datetime import datetime
from datetime import timezone

import pytest

from cartography.intel.cve_metadata.vulnrichment import FETCH_ERRORS
from cartography.intel.cve_metadata.vulnrichment import merge_vulnrichment_into_cves
from cartography.intel.cve_metadata.vulnrichment import read_vulnrichment_archive
from cartography.intel.cve_metadata.vulnrichment import transform_vulnrichment_record
from tests.data.cve_metadata.vulnrichment import ADP_WITHOUT_SSVC_RECORD
from tests.data.cve_metadata.vulnrichment import ARCHIVE_RECORDS
from tests.data.cve_metadata.vulnrichment import build_vulnrichment_archive
from tests.data.cve_metadata.vulnrichment import CISA_ADP_RECORD
from tests.data.cve_metadata.vulnrichment import CISA_ADP_RECORD_WITHOUT_OFFSETS
from tests.data.cve_metadata.vulnrichment import CNA_AND_ADP_SSVC_RECORD
from tests.data.cve_metadata.vulnrichment import CNA_ONLY_RECORD
from tests.data.cve_metadata.vulnrichment import CNA_SSVC_RECORD
from tests.data.cve_metadata.vulnrichment import VULNRICHMENT_COMMIT


@pytest.mark.parametrize(
    "record",
    [CISA_ADP_RECORD, CISA_ADP_RECORD_WITHOUT_OFFSETS],
    ids=["utc", "no-offset-read-as-utc"],
)
def test_transform_record_with_cisa_ssvc(record):
    # Act
    transformed = transform_vulnrichment_record(record)

    # Assert
    assert transformed == {
        "ssvc_exploitation": "active",
        "ssvc_automatable": "yes",
        "ssvc_technical_impact": "total",
        "ssvc_version": "2.0.3",
        "ssvc_timestamp": datetime(2024, 8, 1, 19, 28, 25, 242481, tzinfo=timezone.utc),
        "vulnrichment_updated_at": datetime(
            2024, 10, 29, 14, 7, 56, 381000, tzinfo=timezone.utc
        ),
    }


@pytest.mark.parametrize(
    "record, updated_at",
    [
        (
            CNA_ONLY_RECORD,
            datetime(2024, 5, 28, 18, 59, 27, 726000, tzinfo=timezone.utc),
        ),
        (ADP_WITHOUT_SSVC_RECORD, datetime(2024, 3, 1, tzinfo=timezone.utc)),
        (CNA_SSVC_RECORD, datetime(2024, 4, 1, tzinfo=timezone.utc)),
    ],
    ids=["cna-only", "adp-without-ssvc", "cna-ssvc-only"],
)
def test_transform_record_without_ssvc(record, updated_at):
    # Act
    transformed = transform_vulnrichment_record(record)

    # Assert: the record is known to Vulnrichment, but carries no decision.
    assert transformed.pop("vulnrichment_updated_at") == updated_at
    assert set(transformed.values()) == {None}


def test_transform_record_reads_cisa_ssvc_not_cna():
    # Act
    transformed = transform_vulnrichment_record(CNA_AND_ADP_SSVC_RECORD)

    # Assert
    assert (
        transformed["ssvc_exploitation"],
        transformed["ssvc_automatable"],
        transformed["ssvc_technical_impact"],
        transformed["ssvc_timestamp"],
    ) == ("poc", "yes", "total", datetime(2024, 4, 1, tzinfo=timezone.utc))


def test_read_archive_keeps_graph_cves_and_reads_commit():
    # Arrange: CVE-2024-0002 is not in the graph, CVE-2024-0005 is malformed, and
    # Vulnrichment has no record for CVE-2024-9999.
    archive = build_vulnrichment_archive(
        ARCHIVE_RECORDS,
        extra_files={"2024/0xxx/CVE-2024-0005.json": b"{not json"},
    )
    cve_ids = {"CVE-2023-41782", "CVE-2024-22075", "CVE-2024-0005", "CVE-2024-9999"}

    # Act
    snapshot = read_vulnrichment_archive(io.BytesIO(archive), cve_ids)

    # Assert
    assert snapshot.commit == VULNRICHMENT_COMMIT
    assert set(snapshot.records) == {"CVE-2023-41782", "CVE-2024-22075"}
    assert snapshot.records["CVE-2023-41782"]["ssvc_exploitation"] == "active"
    assert snapshot.records["CVE-2024-22075"]["ssvc_exploitation"] is None


def test_read_archive_without_pax_header_has_no_commit():
    # Arrange
    archive = build_vulnrichment_archive(ARCHIVE_RECORDS, commit=None)

    # Act
    snapshot = read_vulnrichment_archive(io.BytesIO(archive), {"CVE-2023-41782"})

    # Assert
    assert snapshot.commit is None
    assert set(snapshot.records) == {"CVE-2023-41782"}


_ARCHIVE = build_vulnrichment_archive(ARCHIVE_RECORDS)


@pytest.mark.parametrize(
    "archive",
    [
        # A download cut short, at any point, must not read as a smaller archive.
        *(
            pytest.param(_ARCHIVE[: int(len(_ARCHIVE) * keep)], id=f"truncated-{keep}")
            for keep in (0.25, 0.5, 0.75, 0.99)
        ),
        # A complete archive with no CVE records, after a layout change for example,
        # would otherwise unset every SSVC field.
        pytest.param(build_vulnrichment_archive({}), id="no-cve-records"),
    ],
)
def test_read_unusable_archive_raises(archive):
    # Act and assert
    with pytest.raises(FETCH_ERRORS):
        read_vulnrichment_archive(io.BytesIO(archive), {"CVE-2023-41782"})


def test_merge_vulnrichment_without_snapshot_unsets_fields():
    # Arrange
    cves = [{"id": "CVE-2023-41782"}]

    # Act
    merge_vulnrichment_into_cves(cves, None)

    # Assert
    assert cves[0]["ssvc_exploitation"] is None
    assert cves[0]["vulnrichment_updated_at"] is None
