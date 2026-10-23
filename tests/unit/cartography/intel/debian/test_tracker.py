import pytest

from cartography.intel.debian.tracker import read_tracker_records
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

    # Act
    records = read_tracker_records(chunks, CVE_IDS_IN_GRAPH)

    # Assert
    # CVE-2025-30193 is not in the graph, and TEMP-0290435-0B57B5 is not a CVE.
    assert records == [
        (
            "389-ds-base",
            "CVE-2012-0833",
            DEBIAN_TRACKER_DATA["389-ds-base"]["CVE-2012-0833"],
        ),
        (
            "389-ds-base",
            "CVE-2023-1055",
            DEBIAN_TRACKER_DATA["389-ds-base"]["CVE-2023-1055"],
        ),
        ("7zip", "CVE-2026-48092", DEBIAN_TRACKER_DATA["7zip"]["CVE-2026-48092"]),
        ("dnsdist", "CVE-2023-44487", DEBIAN_TRACKER_DATA["dnsdist"]["CVE-2023-44487"]),
        ("tar", "CVE-2005-2541", DEBIAN_TRACKER_DATA["tar"]["CVE-2005-2541"]),
    ]


def test_read_tracker_records_reads_a_number_split_across_chunks():
    # Arrange
    # A number that ends a chunk may continue in the next one.
    chunks = [b'{"tar": {"CVE-2005-2541": 32', b"8228}}"]

    # Act
    records = read_tracker_records(chunks, {"CVE-2005-2541"})

    # Assert
    assert records == [("tar", "CVE-2005-2541", 328228)]


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
