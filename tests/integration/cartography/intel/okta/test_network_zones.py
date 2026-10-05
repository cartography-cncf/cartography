from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.network_zones
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.network_zones import NETWORK_ZONES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _seed_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(stale:OktaNetworkZone {id: 'stale-zone'})
        SET stale.lastupdated = 1
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.okta.network_zones,
    "_get_okta_network_zones",
    new_callable=AsyncMock,
)
def test_sync_okta_network_zones(mock_get_zones, neo4j_session) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_zones.return_value = NETWORK_ZONES

    # Act
    cartography.intel.okta.network_zones.sync_okta_network_zones(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OktaNetworkZone",
        ["id", "type", "usage", "status", "system"],
    ) == {
        ("nzo-corp", "IP", "POLICY", "ACTIVE", False),
        ("nzo-blocked-ips", "IP", "BLOCKLIST", "ACTIVE", True),
        ("nzo-tor", "DYNAMIC", "BLOCKLIST", "ACTIVE", False),
        ("nzo-enhanced-dynamic", "DYNAMIC_V2", "BLOCKLIST", "ACTIVE", True),
    }
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaNetworkZone",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ORG_ID, "nzo-corp"),
        (TEST_ORG_ID, "nzo-blocked-ips"),
        (TEST_ORG_ID, "nzo-tor"),
        (TEST_ORG_ID, "nzo-enhanced-dynamic"),
    }
    record = neo4j_session.run(
        """
        MATCH (z:OktaNetworkZone {id: 'nzo-enhanced-dynamic'})
        RETURN z.ip_service_categories_include AS categories
        """,
    ).single()
    assert record["categories"] == ["ALL_ANONYMIZERS", "FUTURE_CATEGORY"]


@patch.object(
    cartography.intel.okta.network_zones,
    "_get_okta_network_zones",
    new_callable=AsyncMock,
)
def test_sync_okta_network_zones_skips_when_scope_missing(
    mock_get_zones,
    neo4j_session,
) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_zones.side_effect = OktaApiError(
        "/api/v1/zones",
        SimpleNamespace(error_code="E0000006"),
    )

    # Act
    cartography.intel.okta.network_zones.sync_okta_network_zones(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "OktaNetworkZone", ["id"]) == {("stale-zone",)}
