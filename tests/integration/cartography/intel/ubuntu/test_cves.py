from unittest.mock import patch

import cartography.intel.ubuntu.cves
import cartography.intel.ubuntu.feed
import tests.data.ubuntu.cves
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://fake-ubuntu-api.example.com"


def _load_feed(neo4j_session):
    """Load the feed node so that CVE sub-resource relationships can be created."""
    cartography.intel.ubuntu.feed.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )


@patch.object(
    cartography.intel.ubuntu.cves,
    "_fetch_cves",
    return_value=iter([tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE]),
)
def test_sync_ubuntu_cves(mock_api, neo4j_session):
    """
    Ensure that CVE nodes are created with correct properties, the extra CVE label,
    and CVSS v3 fields are populated from nested impact data.
    """
    neo4j_session.run("MATCH (s:UbuntuSyncMetadata) DETACH DELETE s")
    _load_feed(neo4j_session)
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    expected_nodes = {
        ("USV|CVE-2024-1234", "CVE-2024-1234", "high", 8.1),
        ("USV|CVE-2024-5678", "CVE-2024-5678", "medium", 5.3),
        ("USV|CVE-2024-9999", "CVE-2024-9999", "low", 3.7),
    }
    assert (
        check_nodes(neo4j_session, "UbuntuCVE", ["id", "cve_id", "priority", "cvss3"])
        == expected_nodes
    )

    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        ("USV|CVE-2024-1234",),
        ("USV|CVE-2024-5678",),
        ("USV|CVE-2024-9999",),
    }

    record = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'USV|CVE-2024-1234'}) "
        "RETURN n.cve_id, n.attack_vector, n.attack_complexity, n.base_score, n.base_severity",
    ).single()
    assert record["n.cve_id"] == "CVE-2024-1234"
    assert record["n.attack_vector"] == "NETWORK"
    assert record["n.attack_complexity"] == "LOW"
    assert record["n.base_score"] == 8.1
    assert record["n.base_severity"] == "HIGH"

    record = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'USV|CVE-2024-9999'}) RETURN n.attack_vector, n.base_score",
    ).single()
    assert record["n.attack_vector"] is None
    assert record["n.base_score"] is None


@patch.object(
    cartography.intel.ubuntu.cves,
    "_fetch_cves",
    return_value=iter([tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE]),
)
def test_sync_metadata_full_sync(mock_api, neo4j_session):
    """
    After a full sync, metadata should have full_sync_complete=True, offset reset
    to 0, and the watermark set to the max updated_at across all loaded CVEs.
    """
    neo4j_session.run("MATCH (s:UbuntuSyncMetadata) DETACH DELETE s")
    neo4j_session.run("MATCH (n:UbuntuCVE) DETACH DELETE n")
    _load_feed(neo4j_session)
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    mock_api.assert_called_once_with(TEST_API_URL, start_offset=0)

    record = neo4j_session.run(
        "MATCH (s:UbuntuSyncMetadata {id: 'UbuntuCVE_sync_metadata'}) "
        "RETURN s.last_updated_at AS last_updated_at, "
        "       s.full_sync_complete AS full_sync_complete, "
        "       s.full_sync_offset AS full_sync_offset",
    ).single()
    assert record["last_updated_at"] == "2024-03-25T12:00:00"
    assert record["full_sync_complete"] is True
    assert record["full_sync_offset"] == 0


@patch.object(
    cartography.intel.ubuntu.cves,
    "_fetch_cves",
    return_value=iter([tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE]),
)
def test_sync_incremental(mock_api, neo4j_session):
    """
    When full_sync_complete is True, sync takes the incremental path and saves
    the watermark only after all pages are processed (all-or-nothing).
    """
    neo4j_session.run("MATCH (s:UbuntuSyncMetadata) DETACH DELETE s")
    neo4j_session.run("MATCH (n:UbuntuCVE) DETACH DELETE n")
    _load_feed(neo4j_session)
    neo4j_session.run(
        """
        CREATE (s:UbuntuSyncMetadata {
            id: 'UbuntuCVE_sync_metadata',
            full_sync_complete: true,
            full_sync_offset: 0,
            last_updated_at: '2024-01-01T00:00:00'
        })
        """,
    )

    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    mock_api.assert_called_once_with(TEST_API_URL, since="2024-01-01T00:00:00")

    expected_nodes = {
        ("USV|CVE-2024-1234", "high", 8.1),
        ("USV|CVE-2024-5678", "medium", 5.3),
        ("USV|CVE-2024-9999", "low", 3.7),
    }
    assert (
        check_nodes(neo4j_session, "UbuntuCVE", ["id", "priority", "cvss3"])
        == expected_nodes
    )

    record = neo4j_session.run(
        "MATCH (s:UbuntuSyncMetadata {id: 'UbuntuCVE_sync_metadata'}) "
        "RETURN s.last_updated_at AS last_updated_at, "
        "       s.full_sync_complete AS full_sync_complete",
    ).single()
    assert record["last_updated_at"] == "2024-03-25T12:00:00"
    assert record["full_sync_complete"] is True
