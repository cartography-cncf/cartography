from unittest.mock import patch

import cartography.intel.ubuntu.cves
import tests.data.ubuntu.cves
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://fake-ubuntu-api.example.com"


@patch.object(
    cartography.intel.ubuntu.cves,
    "get",
    return_value=tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE,
)
def test_sync_ubuntu_cves(mock_api, neo4j_session):
    """
    Ensure that Ubuntu CVEs are loaded correctly into the graph.
    """
    # Act
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert CVE nodes exist with expected properties
    expected_nodes = {
        ("CVE-2024-1234", "high", 8.1),
        ("CVE-2024-5678", "medium", 5.3),
        ("CVE-2024-9999", "low", 3.7),
    }
    assert check_nodes(neo4j_session, "UbuntuCVE", ["id", "priority", "cvss3"]) == expected_nodes

    # Assert CVE extra label
    expected_cve_label = {
        ("CVE-2024-1234",),
        ("CVE-2024-5678",),
        ("CVE-2024-9999",),
    }
    assert check_nodes(neo4j_session, "CVE", ["id"]) == expected_cve_label

    # Assert CVSS v3 fields are populated for CVE-2024-1234
    result = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'CVE-2024-1234'}) "
        "RETURN n.attack_vector, n.attack_complexity, n.base_score, n.base_severity",
    )
    record = result.single()
    assert record["n.attack_vector"] == "NETWORK"
    assert record["n.attack_complexity"] == "LOW"
    assert record["n.base_score"] == 8.1
    assert record["n.base_severity"] == "HIGH"

    # Assert CVE with no impact data has null CVSS fields
    result = neo4j_session.run(
        "MATCH (n:UbuntuCVE {id: 'CVE-2024-9999'}) RETURN n.attack_vector, n.base_score",
    )
    record = result.single()
    assert record["n.attack_vector"] is None
    assert record["n.base_score"] is None


@patch.object(
    cartography.intel.ubuntu.cves,
    "get",
    return_value=tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE,
)
def test_sync_ubuntu_cves_cleanup(mock_api, neo4j_session):
    """
    Ensure that stale CVE nodes are cleaned up on subsequent syncs.
    """
    # Arrange: first sync
    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        TEST_API_URL,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    assert len(check_nodes(neo4j_session, "UbuntuCVE", ["id"])) == 3

    # Act: second sync with only one CVE
    new_update_tag = TEST_UPDATE_TAG + 1
    with patch.object(
        cartography.intel.ubuntu.cves,
        "get",
        return_value=[tests.data.ubuntu.cves.UBUNTU_CVES_RESPONSE[0]],
    ):
        cartography.intel.ubuntu.cves.sync(
            neo4j_session,
            TEST_API_URL,
            new_update_tag,
            {"UPDATE_TAG": new_update_tag},
        )

    # Assert only the one CVE remains
    expected_nodes = {("CVE-2024-1234",)}
    assert check_nodes(neo4j_session, "UbuntuCVE", ["id"]) == expected_nodes
