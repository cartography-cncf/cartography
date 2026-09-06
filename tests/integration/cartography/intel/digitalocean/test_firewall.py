from unittest.mock import MagicMock

import cartography.intel.digitalocean.compute
import cartography.intel.digitalocean.firewall
import cartography.intel.digitalocean.management
import cartography.intel.digitalocean.platform
import tests.data.digitalocean.compute
import tests.data.digitalocean.firewall
import tests.data.digitalocean.management
import tests.data.digitalocean.platform
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "test-account-uuid"
TEST_PROJECT_ID = "test-project-uuid"
TEST_UPDATE_TAG = 123456789


def _load_prerequisites(neo4j_session):
    account = cartography.intel.digitalocean.platform.transform_account(
        tests.data.digitalocean.platform.ACCOUNT_RESPONSE["account"],
    )
    cartography.intel.digitalocean.platform.load_account(
        neo4j_session,
        [account],
        TEST_UPDATE_TAG,
    )

    projects = cartography.intel.digitalocean.management.transform_projects(
        tests.data.digitalocean.management.PROJECTS_RESPONSE["projects"],
    )
    cartography.intel.digitalocean.management.load_projects(
        neo4j_session,
        projects,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    droplets = cartography.intel.digitalocean.compute.transform_droplets(
        tests.data.digitalocean.compute.DROPLETS_RESPONSE["droplets"],
        TEST_ACCOUNT_ID,
        {
            TEST_PROJECT_ID: [
                {"urn": "do:droplet:568030246"},
            ],
        },
    )
    cartography.intel.digitalocean.compute.load_droplets(
        neo4j_session,
        TEST_ACCOUNT_ID,
        droplets,
        TEST_UPDATE_TAG,
    )


def test_sync_firewalls_with_rules(neo4j_session):
    _load_prerequisites(neo4j_session)
    mock_client = MagicMock()
    mock_client.firewalls.list.return_value = (
        tests.data.digitalocean.firewall.FIREWALLS_RESPONSE
    )

    cartography.intel.digitalocean.firewall.sync(
        neo4j_session,
        mock_client,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": TEST_ACCOUNT_ID},
    )

    firewall_id = "9321bbf2-6ca7-4944-b060-866226df3771"
    _, firewall_rules, ip_ranges = (
        cartography.intel.digitalocean.firewall.transform_firewalls(
            tests.data.digitalocean.firewall.FIREWALLS_RESPONSE["firewalls"],
        )
    )
    rule_ids = {rule["id"] for rule in firewall_rules}

    assert check_nodes(neo4j_session, "DOFirewall", ["id", "name"]) == {
        (firewall_id, "Test Firewall"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DOFirewallRule",
            [
                "id",
                "firewall_id",
                "direction",
                "protocol",
                "ports",
                "fromport",
                "toport",
                "action",
            ],
        )
        == {
            (
                rule["id"],
                firewall_id,
                rule["direction"],
                rule["protocol"],
                rule["ports"],
                rule["fromport"],
                rule["toport"],
                "allow",
            )
            for rule in firewall_rules
        }
    )
    assert check_rels(
        neo4j_session,
        "DOFirewallRule",
        "id",
        "DOFirewall",
        "id",
        "MEMBER_OF_DO_FIREWALL",
    ) == {(rule_id, firewall_id) for rule_id in rule_ids}
    assert check_rels(
        neo4j_session,
        "DOFirewall",
        "id",
        "DODroplet",
        "id",
        "PROTECTS",
    ) == {(firewall_id, 568030246)}

    assert check_nodes(neo4j_session, "DOIpRange", ["id", "range"]) == {
        (ip_range["id"], ip_range["range"]) for ip_range in ip_ranges
    }
    assert check_rels(
        neo4j_session,
        "DOFirewallRule",
        "id",
        "DOIpRange",
        "id",
        "HAS_SOURCE",
    ) == {
        (rule["id"], ip_range_id)
        for rule in firewall_rules
        for ip_range_id in rule.get("source_addresses") or []
    }
    assert check_rels(
        neo4j_session,
        "DOFirewallRule",
        "id",
        "DOIpRange",
        "id",
        "HAS_DESTINATION",
    ) == {
        (rule["id"], ip_range_id)
        for rule in firewall_rules
        for ip_range_id in rule.get("destination_addresses") or []
    }
    assert check_rels(
        neo4j_session,
        "DOFirewallRule",
        "id",
        "DODroplet",
        "id",
        "HAS_SOURCE",
    ) == {
        (rule["id"], droplet_id)
        for rule in firewall_rules
        for droplet_id in rule.get("source_droplet_ids") or []
    }
    assert check_rels(
        neo4j_session,
        "DOFirewallRule",
        "id",
        "DODroplet",
        "id",
        "HAS_DESTINATION",
    ) == {
        (rule["id"], droplet_id)
        for rule in firewall_rules
        for droplet_id in rule.get("destination_droplet_ids") or []
    }

    outbound_rule = next(
        rule for rule in firewall_rules if rule["direction"] == "outbound"
    )
    result = neo4j_session.run(
        "MATCH (r:DOFirewallRule {id: $rule_id}) "
        "RETURN r.destination_addresses AS destination_addresses, "
        "r.destination_load_balancer_uids AS destination_load_balancer_uids, "
        "r.addresses AS deprecated_addresses, "
        "r.load_balancer_uids AS deprecated_load_balancer_uids",
        rule_id=outbound_rule["id"],
    ).single()
    assert result["destination_addresses"] == [
        "0.0.0.0/0",
        "::/0",
    ]
    assert result["destination_load_balancer_uids"] == ["test-load-balancer-uuid"]
    assert result["deprecated_addresses"] is None
    assert result["deprecated_load_balancer_uids"] is None

    icmp_rule = next(rule for rule in firewall_rules if rule["protocol"] == "icmp")
    assert icmp_rule["fromport"] is None
    assert icmp_rule["toport"] is None
