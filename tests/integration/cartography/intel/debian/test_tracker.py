from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
import requests

import cartography.intel.debian.tracker
from cartography.config import Config
from cartography.intel.debian import start_debian_ingestion
from cartography.intel.debian.tracker import DEBIAN_SECURITY_TRACKER_URL
from cartography.intel.debian.tracker import FEED_ID
from cartography.intel.debian.tracker import read_tracker_records
from cartography.intel.debian.tracker import TrackerSnapshot
from tests.data.debian.tracker import CVE_IDS_IN_GRAPH
from tests.data.debian.tracker import tracker_document
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 987654321
LAST_MODIFIED = datetime(2026, 10, 1, 2, 13, 7, tzinfo=timezone.utc)
FETCHED_AT = datetime(2026, 10, 1, 3, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _clear_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _create_cve_nodes(neo4j_session, cve_ids):
    neo4j_session.run(
        """
        UNWIND $cve_ids AS cve_id
        MERGE (c:CVE {id: cve_id})
        SET c.cve_id = cve_id
        """,
        cve_ids=sorted(cve_ids),
    )


def _mock_get(http_session, cve_ids):
    return TrackerSnapshot(
        last_modified=LAST_MODIFIED,
        fetched_at=FETCHED_AT,
        records=read_tracker_records([tracker_document()], cve_ids),
    )


def _sync(neo4j_session, update_tag):
    start_debian_ingestion(
        neo4j_session,
        Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=update_tag,
            debian_security_tracker_enabled=True,
        ),
    )


@patch.object(cartography.intel.debian.tracker, "get", side_effect=_mock_get)
def test_sync_loads_entries_for_cves_in_the_graph(mock_get, neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, CVE_IDS_IN_GRAPH)

    # Act
    _sync(neo4j_session, TEST_UPDATE_TAG)

    # Assert
    feed = neo4j_session.run(
        "MATCH (f:DebianSecurityTrackerFeed) "
        "RETURN f.id AS id, f.url AS url, f.last_modified AS last_modified, "
        "f.fetched_at AS fetched_at",
    ).single()
    assert (
        feed["id"],
        feed["url"],
        feed["last_modified"].to_native(),
        feed["fetched_at"].to_native(),
    ) == (FEED_ID, DEBIAN_SECURITY_TRACKER_URL, LAST_MODIFIED, FETCHED_AT)
    assert check_nodes(
        neo4j_session,
        "DebianSecurityTrackerEntry",
        ["id", "release_version", "status", "urgency", "not_affected"],
    ) == {
        ("bookworm|389-ds-base|CVE-2012-0833", "12", "resolved", "unimportant", True),
        (
            "bookworm|389-ds-base|CVE-2023-1055",
            "12",
            "open",
            "not yet assigned",
            False,
        ),
        (
            "trixie|389-ds-base|CVE-2023-1055",
            "13",
            "resolved",
            "not yet assigned",
            False,
        ),
        ("trixie|7zip|CVE-2026-48092", "13", "open", "unimportant", False),
        ("bookworm|dnsdist|CVE-2023-44487", "12", "open", "end-of-life", False),
        ("bookworm|tar|CVE-2005-2541", "12", "open", "unimportant", False),
        ("sid|tar|CVE-2005-2541", None, "open", "unimportant", False),
    }
    assert check_rels(
        neo4j_session,
        "DebianSecurityTrackerFeed",
        "id",
        "DebianSecurityTrackerEntry",
        "id",
        "RESOURCE",
    ) == {
        (FEED_ID, "bookworm|389-ds-base|CVE-2012-0833"),
        (FEED_ID, "bookworm|389-ds-base|CVE-2023-1055"),
        (FEED_ID, "trixie|389-ds-base|CVE-2023-1055"),
        (FEED_ID, "trixie|7zip|CVE-2026-48092"),
        (FEED_ID, "bookworm|dnsdist|CVE-2023-44487"),
        (FEED_ID, "bookworm|tar|CVE-2005-2541"),
        (FEED_ID, "sid|tar|CVE-2005-2541"),
    }
    # Entries are not CVE nodes, so they do not widen the scope of later syncs.
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        (cve_id,) for cve_id in CVE_IDS_IN_GRAPH
    }


@patch.object(cartography.intel.debian.tracker, "get", side_effect=_mock_get)
def test_sync_removes_entries_of_cves_that_left_the_graph(mock_get, neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, CVE_IDS_IN_GRAPH)
    _sync(neo4j_session, TEST_UPDATE_TAG)
    neo4j_session.run(
        "MATCH (c:CVE) WHERE c.id <> 'CVE-2005-2541' DETACH DELETE c",
    )

    # Act
    _sync(neo4j_session, TEST_UPDATE_TAG_2)

    # Assert
    assert check_nodes(
        neo4j_session,
        "DebianSecurityTrackerEntry",
        ["id", "lastupdated"],
    ) == {
        ("bookworm|tar|CVE-2005-2541", TEST_UPDATE_TAG_2),
        ("sid|tar|CVE-2005-2541", TEST_UPDATE_TAG_2),
    }


def test_sync_with_no_cves_needs_no_download(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, CVE_IDS_IN_GRAPH)
    with patch.object(
        cartography.intel.debian.tracker,
        "get",
        side_effect=_mock_get,
    ):
        _sync(neo4j_session, TEST_UPDATE_TAG)
    neo4j_session.run("MATCH (c:CVE) DETACH DELETE c")

    # Act
    with patch.object(
        cartography.intel.debian.tracker,
        "get",
        side_effect=requests.exceptions.ConnectionError("tracker unreachable"),
    ):
        _sync(neo4j_session, TEST_UPDATE_TAG_2)

    # Assert
    assert check_nodes(neo4j_session, "DebianSecurityTrackerEntry", ["id"]) == set()


def test_failed_download_keeps_the_previous_entries(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, CVE_IDS_IN_GRAPH)
    with patch.object(
        cartography.intel.debian.tracker,
        "get",
        side_effect=_mock_get,
    ):
        _sync(neo4j_session, TEST_UPDATE_TAG)

    # Act and assert
    with patch.object(
        cartography.intel.debian.tracker,
        "get",
        side_effect=requests.exceptions.ConnectionError("connection reset"),
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            _sync(neo4j_session, TEST_UPDATE_TAG_2)

    assert len(check_nodes(neo4j_session, "DebianSecurityTrackerEntry", ["id"])) == 7
