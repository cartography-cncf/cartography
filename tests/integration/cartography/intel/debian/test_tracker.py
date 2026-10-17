import io
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
import requests

from cartography.config import Config
from cartography.intel.debian import start_debian_ingestion
from cartography.intel.debian.tracker import DEBIAN_SECURITY_TRACKER_URL
from cartography.intel.debian.tracker import FEED_ID
from tests.data.debian.tracker import tracker_document
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 987654321
LAST_MODIFIED_HEADER = "Thu, 01 Oct 2026 02:13:07 GMT"
LAST_MODIFIED = datetime(2026, 10, 1, 2, 13, 7, tzinfo=timezone.utc)


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
        cve_ids=cve_ids,
    )


def _tracker_response(body: bytes, status_code: int = 200) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.raw = io.BytesIO(body)
    response.headers["Last-Modified"] = LAST_MODIFIED_HEADER
    return response


def _serve_tracker(reply: requests.Response | Exception):
    # A mock raises an exception it finds in side_effect and returns anything else.
    return patch.object(requests.Session, "get", side_effect=[reply])


def _sync(neo4j_session, update_tag):
    start_debian_ingestion(
        neo4j_session,
        Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=update_tag,
            debian_security_tracker_enabled=True,
        ),
    )


def test_sync_loads_entries_for_cves_in_the_graph(neo4j_session):
    # Arrange
    _create_cve_nodes(
        neo4j_session,
        [
            "CVE-2005-2541",
            "CVE-2012-0833",
            "CVE-2023-1055",
            "CVE-2023-44487",
            "CVE-2026-48092",
        ],
    )
    sync_started = datetime.now(timezone.utc)

    # Act
    with _serve_tracker(_tracker_response(tracker_document())):
        _sync(neo4j_session, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(
        neo4j_session,
        "DebianSecurityTrackerFeed",
        ["id", "url", "last_modified"],
    ) == {(FEED_ID, DEBIAN_SECURITY_TRACKER_URL, LAST_MODIFIED)}
    fetched_at = neo4j_session.run(
        "MATCH (f:DebianSecurityTrackerFeed) RETURN f.fetched_at AS fetched_at",
    ).single()["fetched_at"]
    assert fetched_at.to_native() >= sync_started
    assert check_nodes(
        neo4j_session,
        "DebianSecurityTrackerEntry",
        [
            "id",
            "cve_id",
            "source_package",
            "release",
            "release_version",
            "status",
            "urgency",
            "fixed_version",
            "not_affected",
            "nodsa",
            "nodsa_reason",
            "next_point_update",
            "debianbug",
        ],
    ) == {
        (
            "bookworm|389-ds-base|CVE-2012-0833",
            "CVE-2012-0833",
            "389-ds-base",
            "bookworm",
            "12",
            "resolved",
            "unimportant",
            "0",
            True,
            None,
            None,
            False,
            None,
        ),
        (
            "bookworm|389-ds-base|CVE-2023-1055",
            "CVE-2023-1055",
            "389-ds-base",
            "bookworm",
            "12",
            "open",
            "not yet assigned",
            None,
            False,
            "Minor issue",
            "",
            False,
            1034891,
        ),
        (
            "trixie|389-ds-base|CVE-2023-1055",
            "CVE-2023-1055",
            "389-ds-base",
            "trixie",
            "13",
            "resolved",
            "not yet assigned",
            "2.3.4+dfsg1-1",
            False,
            None,
            None,
            False,
            1034891,
        ),
        (
            "trixie|7zip|CVE-2026-48092",
            "CVE-2026-48092",
            "7zip",
            "trixie",
            "13",
            "open",
            "unimportant",
            None,
            False,
            None,
            None,
            True,
            None,
        ),
        (
            "bookworm|dnsdist|CVE-2023-44487",
            "CVE-2023-44487",
            "dnsdist",
            "bookworm",
            "12",
            "open",
            "end-of-life",
            None,
            False,
            None,
            None,
            False,
            None,
        ),
        (
            "bookworm|tar|CVE-2005-2541",
            "CVE-2005-2541",
            "tar",
            "bookworm",
            "12",
            "open",
            "unimportant",
            None,
            False,
            None,
            None,
            False,
            328228,
        ),
        (
            "sid|tar|CVE-2005-2541",
            "CVE-2005-2541",
            "tar",
            "sid",
            None,
            "open",
            "unimportant",
            None,
            False,
            None,
            None,
            False,
            328228,
        ),
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
        ("CVE-2005-2541",),
        ("CVE-2012-0833",),
        ("CVE-2023-1055",),
        ("CVE-2023-44487",),
        ("CVE-2026-48092",),
    }


def test_sync_removes_entries_of_cves_that_left_the_graph(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, ["CVE-2005-2541", "CVE-2023-44487"])
    with _serve_tracker(_tracker_response(tracker_document())):
        _sync(neo4j_session, TEST_UPDATE_TAG)
    neo4j_session.run("MATCH (c:CVE {id: 'CVE-2023-44487'}) DETACH DELETE c")

    # Act
    with _serve_tracker(_tracker_response(tracker_document())):
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


def test_sync_with_no_cves_removes_entries_without_a_download(neo4j_session):
    # Arrange
    _create_cve_nodes(neo4j_session, ["CVE-2005-2541"])
    with _serve_tracker(_tracker_response(tracker_document())):
        _sync(neo4j_session, TEST_UPDATE_TAG)
    neo4j_session.run("MATCH (c:CVE) DETACH DELETE c")

    # Act
    with _serve_tracker(requests.exceptions.ConnectionError("tracker unreachable")):
        _sync(neo4j_session, TEST_UPDATE_TAG_2)

    # Assert
    assert check_nodes(neo4j_session, "DebianSecurityTrackerEntry", ["id"]) == set()


@pytest.mark.parametrize(
    ("failed_reply", "error"),
    [
        pytest.param(
            lambda: requests.exceptions.ConnectionError("connection reset"),
            requests.exceptions.ConnectionError,
            id="connection-error",
        ),
        pytest.param(
            lambda: _tracker_response(b"", status_code=503),
            requests.exceptions.HTTPError,
            id="server-error",
        ),
        # Valid JSON, but loading nothing would let cleanup remove every entry.
        pytest.param(
            lambda: _tracker_response(b"{}"),
            ValueError,
            id="empty-document",
        ),
    ],
)
def test_failed_download_keeps_the_previous_entries(
    neo4j_session,
    failed_reply,
    error,
):
    # Arrange
    _create_cve_nodes(neo4j_session, ["CVE-2005-2541"])
    with _serve_tracker(_tracker_response(tracker_document())):
        _sync(neo4j_session, TEST_UPDATE_TAG)

    # Act and assert
    with _serve_tracker(failed_reply()), pytest.raises(error):
        _sync(neo4j_session, TEST_UPDATE_TAG_2)

    assert check_nodes(
        neo4j_session,
        "DebianSecurityTrackerEntry",
        ["id", "lastupdated"],
    ) == {
        ("bookworm|tar|CVE-2005-2541", TEST_UPDATE_TAG),
        ("sid|tar|CVE-2005-2541", TEST_UPDATE_TAG),
    }
