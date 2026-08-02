from unittest.mock import patch

import cartography.intel.cloudflare.firewallrules
import tests.data.cloudflare.accounts
import tests.data.cloudflare.firewallrules
import tests.data.cloudflare.zones
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.cartography.intel.cloudflare.test_zones import (
    _ensure_local_neo4j_has_test_zones,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]
ZONE_ID = tests.data.cloudflare.zones.CLOUDFLARE_ZONES[0]["id"]


@patch.object(
    cartography.intel.cloudflare.firewallrules,
    "get",
    return_value=tests.data.cloudflare.firewallrules.CLOUDFLARE_FIREWALLRULES,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_firewallrules(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that zone firewall rules actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.firewallrules.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert FirewallRules exist
    expected_nodes = {
        (
            "4b7f36f8b5b8c5d6e7f8a9b0c1d2e3f4",
            "block",
            "Block known bad IPs",
            "3a1c5f9e7b3a4c5d6e7f8a9b0c1d2e3f",
            "ip.src in {1.2.3.4 5.6.7.8}",
        ),
        (
            "9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a",
            "challenge",
            "Challenge traffic from suspicious ASNs",
            "6e5d4c3b2a1f9e8d7c6b5a4f3e2d1c0b",
            "ip.geoip.asnum in {64512}",
        ),
        (
            "a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "allow",
            None,
            None,
            None,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareFirewallRule",
            ["id", "action", "description", "filter_id", "filter_expression"],
        )
        == expected_nodes
    )

    # Assert FirewallRules are connected with Account (the tenant)
    expected_account_rels = {
        ("4b7f36f8b5b8c5d6e7f8a9b0c1d2e3f4", ACCOUNT_ID),
        ("9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a", ACCOUNT_ID),
        ("a1b2c3d4e5f60718293a4b5c6d7e8f90", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareFirewallRule",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_account_rels
    )

    # Assert FirewallRules are connected with Zone
    expected_zone_rels = {
        ("4b7f36f8b5b8c5d6e7f8a9b0c1d2e3f4", ZONE_ID),
        ("9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a", ZONE_ID),
        ("a1b2c3d4e5f60718293a4b5c6d7e8f90", ZONE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareFirewallRule",
            "id",
            "CloudflareZone",
            "id",
            "HAS_FIREWALL_RULE",
            rel_direction_right=False,
        )
        == expected_zone_rels
    )


@patch.object(
    cartography.intel.cloudflare.firewallrules,
    "get",
    return_value=tests.data.cloudflare.firewallrules.CLOUDFLARE_FIREWALLRULES,
)
@patch("cloudflare.Cloudflare")
def test_cloudflare_firewallrules_cleanup_removes_stale(
    mock_cloudflare, mock_api, neo4j_session
):
    """
    Ensure that firewall rules the API no longer returns are removed by the
    account-scoped cleanup
    """

    # Arrange: seed the graph with a rule the API still returns and a stale one
    # from a previous update tag
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    neo4j_session.run(
        """
        MATCH (z:CloudflareZone {id: $zone_id})
        MATCH (a:CloudflareAccount {id: $account_id})
        MERGE (stale:CloudflareFirewallRule {id: 'stale-rule'})
        SET stale.lastupdated = $old_update_tag
        MERGE (a)-[r1:RESOURCE]->(stale)
        SET r1.lastupdated = $old_update_tag
        MERGE (z)-[r2:HAS_FIREWALL_RULE]->(stale)
        SET r2.lastupdated = $old_update_tag
        """,
        zone_id=ZONE_ID,
        account_id=ACCOUNT_ID,
        old_update_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.cloudflare.firewallrules.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert the stale rule is gone and the current ones remain
    remaining = {
        rule_id
        for (rule_id,) in check_nodes(neo4j_session, "CloudflareFirewallRule", ["id"])
    }
    assert "stale-rule" not in remaining
    assert "4b7f36f8b5b8c5d6e7f8a9b0c1d2e3f4" in remaining
    assert "9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a" in remaining
    assert "a1b2c3d4e5f60718293a4b5c6d7e8f90" in remaining
