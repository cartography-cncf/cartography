from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.crowdstrike.endpoints
import cartography.intel.crowdstrike.spotlight
from tests.data.crowdstrike.endpoints import GET_HOSTS
from tests.data.crowdstrike.spotlight import GET_SPOTLIGHT_VULNERABILITIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.crowdstrike.spotlight, "Spotlight_Vulnerabilities")
@patch.object(
    cartography.intel.crowdstrike.spotlight,
    "get_spotlight_vulnerabilities",
    return_value=GET_SPOTLIGHT_VULNERABILITIES,
)
@patch.object(
    cartography.intel.crowdstrike.spotlight,
    "get_spotlight_vulnerability_ids",
    return_value=[["dummy-id"]],
)
@patch.object(cartography.intel.crowdstrike.endpoints, "Hosts")
@patch.object(
    cartography.intel.crowdstrike.endpoints, "get_hosts", return_value=GET_HOSTS
)
@patch.object(
    cartography.intel.crowdstrike.endpoints, "get_host_ids", return_value=[["dummy-id"]]
)
def test_sync_spotlight_vulnerabilities(
    mock_host_ids,
    mock_hosts,
    mock_hosts_cls,
    mock_vuln_ids,
    mock_vulns,
    mock_spotlight_cls,
    neo4j_session,
):
    """
    Ensure that syncing hosts then vulnerabilities creates the expected nodes and relationships.
    """
    authorization = MagicMock()

    # Sync hosts first (dependency for vulnerability relationships)
    cartography.intel.crowdstrike.endpoints.sync_hosts(
        neo4j_session,
        TEST_UPDATE_TAG,
        authorization,
    )

    # Sync vulnerabilities
    cartography.intel.crowdstrike.spotlight.sync_vulnerabilities(
        neo4j_session,
        TEST_UPDATE_TAG,
        authorization,
    )

    # Verify CrowdstrikeHost nodes
    assert check_nodes(neo4j_session, "CrowdstrikeHost", ["id"]) == {
        ("00000000000000000000000000000000",),
    }

    # Verify SpotlightVulnerability nodes
    assert check_nodes(
        neo4j_session, "SpotlightVulnerability", ["id", "cve_id", "status"]
    ) == {
        (
            "00000000000000000000000000000000_00000000000000000000000000000000",
            "CVE-2019-5094",
            "open",
        ),
    }

    # Verify CVE nodes
    assert check_nodes(neo4j_session, "CVE", ["id", "base_score"]) == {
        ("CVE-2019-5094", 6.7),
    }

    # Verify CrowdstrikeHost -[:HAS_VULNERABILITY]-> SpotlightVulnerability
    assert check_rels(
        neo4j_session,
        "CrowdstrikeHost",
        "id",
        "SpotlightVulnerability",
        "id",
        "HAS_VULNERABILITY",
        rel_direction_right=True,
    ) == {
        (
            "00000000000000000000000000000000",
            "00000000000000000000000000000000_00000000000000000000000000000000",
        ),
    }

    # Verify SpotlightVulnerability -[:HAS_CVE]-> CVE
    assert check_rels(
        neo4j_session,
        "SpotlightVulnerability",
        "id",
        "CVE",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {
        (
            "00000000000000000000000000000000_00000000000000000000000000000000",
            "CVE-2019-5094",
        ),
    }
