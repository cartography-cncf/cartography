import pytest

from cartography.intel.debian.tracker import _JSONStream
from cartography.intel.debian.tracker import read_tracker_records
from cartography.intel.debian.tracker import transform
from tests.data.debian.tracker import CVE_IDS_IN_GRAPH
from tests.data.debian.tracker import DEBIAN_TRACKER_DATA
from tests.data.debian.tracker import tracker_document


def _chunks(document: bytes, size: int) -> list[bytes]:
    return [document[i : i + size] for i in range(0, len(document), size)]


@pytest.mark.parametrize("indent", [None, 2])
@pytest.mark.parametrize("chunk_size", [1, 4096])
def test_read_tracker_records_keeps_cves_in_the_graph(indent, chunk_size):
    # Arrange
    # One-byte chunks split every token and the multi-byte character in a description.
    chunks = _chunks(tracker_document(indent), chunk_size)
    expected = [
        (source_package, vuln_id, record)
        for source_package, records in DEBIAN_TRACKER_DATA.items()
        for vuln_id, record in records.items()
        if vuln_id in CVE_IDS_IN_GRAPH
    ]

    # Act
    records = read_tracker_records(chunks, CVE_IDS_IN_GRAPH)

    # Assert
    assert records == expected


@pytest.mark.parametrize(
    "document",
    [
        pytest.param(tracker_document()[:-1], id="missing-last-byte"),
        pytest.param(tracker_document()[:-1000], id="truncated"),
        pytest.param(tracker_document() + b"{}", id="trailing-data"),
        # Valid JSON, but loading no records would remove every previous entry.
        pytest.param(b"{}", id="no-packages"),
        pytest.param(b'{"tar": {}}', id="no-records"),
    ],
)
def test_read_tracker_records_rejects_a_bad_document(document):
    # Act and assert
    with pytest.raises(ValueError):
        read_tracker_records(_chunks(document, 64), CVE_IDS_IN_GRAPH)


def test_transform():
    # Arrange
    records = read_tracker_records([tracker_document()], CVE_IDS_IN_GRAPH)

    # Act
    entries = transform(records)

    # Assert
    unset = {
        "fixed_version": None,
        "not_affected": False,
        "nodsa": None,
        "nodsa_reason": None,
        "next_point_update": False,
        "debianbug": None,
    }
    assert entries == [
        {
            **unset,
            "id": "bookworm|389-ds-base|CVE-2012-0833",
            "cve_id": "CVE-2012-0833",
            "source_package": "389-ds-base",
            "release": "bookworm",
            "release_version": "12",
            "status": "resolved",
            "urgency": "unimportant",
            "fixed_version": "0",
            "not_affected": True,
        },
        {
            **unset,
            "id": "bookworm|389-ds-base|CVE-2023-1055",
            "cve_id": "CVE-2023-1055",
            "source_package": "389-ds-base",
            "release": "bookworm",
            "release_version": "12",
            "status": "open",
            "urgency": "not yet assigned",
            "nodsa": "Minor issue",
            "nodsa_reason": "",
            "debianbug": 1034891,
        },
        {
            **unset,
            "id": "trixie|389-ds-base|CVE-2023-1055",
            "cve_id": "CVE-2023-1055",
            "source_package": "389-ds-base",
            "release": "trixie",
            "release_version": "13",
            "status": "resolved",
            "urgency": "not yet assigned",
            "fixed_version": "2.3.4+dfsg1-1",
            "debianbug": 1034891,
        },
        {
            **unset,
            "id": "trixie|7zip|CVE-2026-48092",
            "cve_id": "CVE-2026-48092",
            "source_package": "7zip",
            "release": "trixie",
            "release_version": "13",
            "status": "open",
            "urgency": "unimportant",
            "next_point_update": True,
        },
        {
            **unset,
            "id": "bookworm|dnsdist|CVE-2023-44487",
            "cve_id": "CVE-2023-44487",
            "source_package": "dnsdist",
            "release": "bookworm",
            "release_version": "12",
            "status": "open",
            "urgency": "end-of-life",
        },
        {
            **unset,
            "id": "bookworm|tar|CVE-2005-2541",
            "cve_id": "CVE-2005-2541",
            "source_package": "tar",
            "release": "bookworm",
            "release_version": "12",
            "status": "open",
            "urgency": "unimportant",
            "debianbug": 328228,
        },
        {
            **unset,
            "id": "sid|tar|CVE-2005-2541",
            "cve_id": "CVE-2005-2541",
            "source_package": "tar",
            "release": "sid",
            "release_version": None,
            "status": "open",
            "urgency": "unimportant",
            "debianbug": 328228,
        },
    ]


def test_json_stream_reads_a_number_split_across_chunks():
    # Arrange
    stream = _JSONStream(['{"debianbug": 10', "34891}"])

    # Act
    members = [(key, stream.value()) for key in stream.members()]

    # Assert
    assert members == [("debianbug", 1034891)]
