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
    zones = {
        record["id"]: record["zone"]
        for record in neo4j_session.run(
            """
            MATCH (z:OktaNetworkZone)
            RETURN z.id AS id, {
                gateways: z.gateways,
                proxies: z.proxies,
                use_as_exempt_list: z.use_as_exempt_list,
                asns_include: z.asns_include,
                asns_exclude: z.asns_exclude,
                locations_include: z.locations_include,
                locations_exclude: z.locations_exclude,
                proxy_type: z.proxy_type,
                ip_service_categories_include: z.ip_service_categories_include,
                ip_service_categories_exclude: z.ip_service_categories_exclude
            } AS zone
            """,
        )
    }
    assert zones["nzo-corp"]["gateways"] == [
        "198.51.100.0/24",
        "203.0.113.10-203.0.113.20",
    ]
    assert zones["nzo-corp"]["proxies"] == ["192.0.2.10/32"]
    assert zones["nzo-corp"]["use_as_exempt_list"] is False
    assert zones["nzo-blocked-ips"]["gateways"] == ["233.252.0.0/24"]
    assert zones["nzo-tor"]["asns_include"] == ["64496", "64497"]
    assert zones["nzo-tor"]["locations_include"] == ["AQ", "US-AK"]
    assert zones["nzo-tor"]["proxy_type"] == "TorAnonymizer"
    assert not zones["nzo-tor"]["asns_exclude"]
    assert not zones["nzo-tor"]["locations_exclude"]
    assert not zones["nzo-enhanced-dynamic"]["asns_include"]
    assert zones["nzo-enhanced-dynamic"]["asns_exclude"] == ["64498"]
    assert not zones["nzo-enhanced-dynamic"]["locations_include"]
    assert zones["nzo-enhanced-dynamic"]["locations_exclude"] == ["CA"]
    assert zones["nzo-enhanced-dynamic"]["ip_service_categories_include"] == [
        "ALL_ANONYMIZERS",
        "FUTURE_CATEGORY",
    ]
    assert not zones["nzo-enhanced-dynamic"]["ip_service_categories_exclude"]


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
