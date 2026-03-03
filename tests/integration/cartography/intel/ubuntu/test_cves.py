from unittest.mock import patch

import cartography.intel.ubuntu.cves
import tests.data.ubuntu.cves
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://fake-ubuntu-api.example.com"


@patch.object(
    cartography.intel.ubuntu.cves,
    "get_updated_since",
    return_value=tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE,
)
def test_sync_ubuntu_cves(mock_api, neo4j_session):
    """
    Ensure that CVE nodes are created with correct properties, the extra CVE label,
    and CVSS v3 fields are populated from nested impact data.
    """
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Nodes exist with key business properties
    expected_nodes = {
        ("CVE-2024-1234", "high", 8.1),
        ("CVE-2024-5678", "medium", 5.3),
        ("CVE-2024-9999", "low", 3.7),
    }
    assert (
        check_nodes(neo4j_session, "UbuntuCVE", ["id", "priority", "cvss3"])
        == expected_nodes
    )

    # Extra CVE label is applied
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {
        ("CVE-2024-1234",),
        ("CVE-2024-5678",),
        ("CVE-2024-9999",),
    }

    # CVSS v3 fields populated from nested impact data
    record = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'CVE-2024-1234'}) "
        "RETURN n.attack_vector, n.attack_complexity, n.base_score, n.base_severity",
    ).single()
    assert record["n.attack_vector"] == "NETWORK"
    assert record["n.attack_complexity"] == "LOW"
    assert record["n.base_score"] == 8.1
    assert record["n.base_severity"] == "HIGH"

    # CVE with empty impact has null CVSS fields
    record = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'CVE-2024-9999'}) RETURN n.attack_vector, n.base_score",
    ).single()
    assert record["n.attack_vector"] is None
    assert record["n.base_score"] is None


@patch.object(
    cartography.intel.ubuntu.cves,
    "get_updated_since",
    return_value=tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE,
)
def test_sync_metadata_written(mock_api, neo4j_session):
    """
    Ensure that an UbuntuSyncMetadata node is created with the correct watermark
    so that subsequent syncs can run incrementally.
    """
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    record = neo4j_session.run(
        "MATCH (s:UbuntuSyncMetadata {id: 'UbuntuCVE_sync_metadata'}) "
        "RETURN s.last_updated_at AS last_updated_at",
    ).single()
    assert record["last_updated_at"] == "2024-03-25T12:00:00"
