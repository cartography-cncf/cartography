from unittest.mock import patch

import cartography.intel.cloudflare.accounts
import cartography.intel.cloudflare.rulesets
import cartography.intel.cloudflare.zones
import tests.data.cloudflare.accounts
import tests.data.cloudflare.rulesets
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

# A second tenant, used to prove that a shared managed ruleset does not merge the
# deployments of two accounts read with the same token.
OTHER_ACCOUNT = {"id": "9b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e", "name": "Flanders Org"}
OTHER_ZONE = {"id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d", "name": "flanders.corp"}

ACCOUNT_WAF_RULESET_ID = "c4e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
CUSTOM_FIREWALL_RULESET_ID = "d5f1a2b3c4e5d6f7a8b9c0d1e2f3a4b5"
MANAGED_RULESET_ID = "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6"
CACHE_RULESET_ID = "f7b3c4d5e6a7b8c9d0e1f2a3b4c5d6e7"

# Deployments, keyed by the scope they apply to.
ACCOUNT_WAF_DEPLOYMENT = f"{ACCOUNT_ID}/{ACCOUNT_WAF_RULESET_ID}"
ACCOUNT_MANAGED_DEPLOYMENT = f"{ACCOUNT_ID}/{MANAGED_RULESET_ID}"
ZONE_FIREWALL_DEPLOYMENT = f"{ZONE_ID}/{CUSTOM_FIREWALL_RULESET_ID}"
ZONE_MANAGED_DEPLOYMENT = f"{ZONE_ID}/{MANAGED_RULESET_ID}"
ZONE_CACHE_DEPLOYMENT = f"{ZONE_ID}/{CACHE_RULESET_ID}"

# Rule IDs as the API returns them, before they are qualified by deployment.
ACCOUNT_EXECUTE_RULE_ID = "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e701"
BLOCK_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c501"
CHALLENGE_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c502"
ZONE_EXECUTE_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c503"
CACHE_RULE_ID = "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d601"


def _fake_rulesets(client, account_id, zone_id):
    if zone_id:
        return tests.data.cloudflare.rulesets.CLOUDFLARE_ZONE_RULESETS
    return tests.data.cloudflare.rulesets.CLOUDFLARE_ACCOUNT_RULESETS


def _fake_ruleset_rules(client, account_id, zone_id, ruleset_id):
    return tests.data.cloudflare.rulesets.CLOUDFLARE_RULESET_RULES[ruleset_id]


def _ensure_local_neo4j_has_test_rulesets(neo4j_session):
    cartography.intel.cloudflare.rulesets.load_rulesets(
        neo4j_session,
        cartography.intel.cloudflare.rulesets.transform_rulesets(
            tests.data.cloudflare.rulesets.CLOUDFLARE_ZONE_RULESETS,
            ACCOUNT_ID,
            ZONE_ID,
        ),
        ACCOUNT_ID,
        ZONE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_ruleset_rules",
    side_effect=_fake_ruleset_rules,
)
@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_rulesets",
    side_effect=_fake_rulesets,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_rulesets(
    mock_cloudflare, mock_rulesets, mock_rules, neo4j_session
):
    """
    Ensure that account-level and zone-level rulesets and their rules get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.rulesets.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert rulesets from both scopes exist, each keyed by its deployment. The
    # managed ruleset is deployed twice and keeps its API ID in both nodes.
    expected_nodes = {
        (
            ACCOUNT_WAF_DEPLOYMENT,
            ACCOUNT_WAF_RULESET_ID,
            "Springfield account WAF",
            "root",
            "account",
        ),
        (
            ACCOUNT_MANAGED_DEPLOYMENT,
            MANAGED_RULESET_ID,
            "Cloudflare Managed Ruleset",
            "managed",
            "account",
        ),
        (
            ZONE_FIREWALL_DEPLOYMENT,
            CUSTOM_FIREWALL_RULESET_ID,
            "Simpson custom firewall",
            "zone",
            "zone",
        ),
        (
            ZONE_MANAGED_DEPLOYMENT,
            MANAGED_RULESET_ID,
            "Cloudflare Managed Ruleset",
            "managed",
            "zone",
        ),
        (
            ZONE_CACHE_DEPLOYMENT,
            CACHE_RULESET_ID,
            "Simpson cache settings",
            "zone",
            "zone",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareRuleset",
            ["id", "ruleset_id", "name", "kind", "scope"],
        )
        == expected_nodes
    )

    # Assert every deployment is owned by the Account
    assert check_rels(
        neo4j_session,
        "CloudflareRuleset",
        "id",
        "CloudflareAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (ACCOUNT_WAF_DEPLOYMENT, ACCOUNT_ID),
        (ACCOUNT_MANAGED_DEPLOYMENT, ACCOUNT_ID),
        (ZONE_FIREWALL_DEPLOYMENT, ACCOUNT_ID),
        (ZONE_MANAGED_DEPLOYMENT, ACCOUNT_ID),
        (ZONE_CACHE_DEPLOYMENT, ACCOUNT_ID),
    }

    # Assert only the zone-level deployments are attached to the Zone: an
    # account-level ruleset is not tied to a single zone
    assert check_rels(
        neo4j_session,
        "CloudflareRuleset",
        "id",
        "CloudflareZone",
        "id",
        "HAS_RULESET",
        rel_direction_right=False,
    ) == {
        (ZONE_FIREWALL_DEPLOYMENT, ZONE_ID),
        (ZONE_MANAGED_DEPLOYMENT, ZONE_ID),
        (ZONE_CACHE_DEPLOYMENT, ZONE_ID),
    }

    # Assert the vendor-owned contents of the managed ruleset were not ingested in
    # either scope: both of its deployments hold no rule at all, while the
    # customer-authored deployments do
    result = neo4j_session.run(
        """
        MATCH (r:CloudflareRuleset)
        OPTIONAL MATCH (r)-[:HAS_RULE]->(rule:CloudflareRulesetRule)
        RETURN r.id AS id, count(rule) AS rules
        """
    )
    assert {(record["id"], record["rules"]) for record in result} == {
        (ACCOUNT_WAF_DEPLOYMENT, 1),
        (ACCOUNT_MANAGED_DEPLOYMENT, 0),
        (ZONE_FIREWALL_DEPLOYMENT, 3),
        (ZONE_MANAGED_DEPLOYMENT, 0),
        (ZONE_CACHE_DEPLOYMENT, 1),
    }

    # Rule IDs are qualified by their deployment too: a rule only exists as part
    # of one, and its API ID is only unique within one.
    expected_rules = {
        (
            f"{ACCOUNT_WAF_DEPLOYMENT}/{ACCOUNT_EXECUTE_RULE_ID}",
            ACCOUNT_EXECUTE_RULE_ID,
            "execute",
            True,
        ),
        (f"{ZONE_FIREWALL_DEPLOYMENT}/{BLOCK_RULE_ID}", BLOCK_RULE_ID, "block", True),
        (
            f"{ZONE_FIREWALL_DEPLOYMENT}/{CHALLENGE_RULE_ID}",
            CHALLENGE_RULE_ID,
            "managed_challenge",
            True,
        ),
        (
            f"{ZONE_FIREWALL_DEPLOYMENT}/{ZONE_EXECUTE_RULE_ID}",
            ZONE_EXECUTE_RULE_ID,
            "execute",
            True,
        ),
        (
            f"{ZONE_CACHE_DEPLOYMENT}/{CACHE_RULE_ID}",
            CACHE_RULE_ID,
            "set_cache_settings",
            True,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareRulesetRule",
            ["id", "rule_id", "action", "enabled"],
        )
        == expected_rules
    )

    # Assert rules are connected with the deployment they were read from
    assert check_rels(
        neo4j_session,
        "CloudflareRulesetRule",
        "id",
        "CloudflareRuleset",
        "id",
        "HAS_RULE",
        rel_direction_right=False,
    ) == {
        (f"{ACCOUNT_WAF_DEPLOYMENT}/{ACCOUNT_EXECUTE_RULE_ID}", ACCOUNT_WAF_DEPLOYMENT),
        (f"{ZONE_FIREWALL_DEPLOYMENT}/{BLOCK_RULE_ID}", ZONE_FIREWALL_DEPLOYMENT),
        (f"{ZONE_FIREWALL_DEPLOYMENT}/{CHALLENGE_RULE_ID}", ZONE_FIREWALL_DEPLOYMENT),
        (
            f"{ZONE_FIREWALL_DEPLOYMENT}/{ZONE_EXECUTE_RULE_ID}",
            ZONE_FIREWALL_DEPLOYMENT,
        ),
        (f"{ZONE_CACHE_DEPLOYMENT}/{CACHE_RULE_ID}", ZONE_CACHE_DEPLOYMENT),
    }

    # Assert each `execute` rule turns on exactly one deployment, the one in its
    # own scope: the account-level rule targets the account-level deployment of
    # the managed ruleset, the zone-level rule the zone-level one
    assert check_rels(
        neo4j_session,
        "CloudflareRulesetRule",
        "id",
        "CloudflareRuleset",
        "id",
        "EXECUTES",
        rel_direction_right=True,
    ) == {
        (
            f"{ACCOUNT_WAF_DEPLOYMENT}/{ACCOUNT_EXECUTE_RULE_ID}",
            ACCOUNT_MANAGED_DEPLOYMENT,
        ),
        (f"{ZONE_FIREWALL_DEPLOYMENT}/{ZONE_EXECUTE_RULE_ID}", ZONE_MANAGED_DEPLOYMENT),
    }

    # Assert the raw API ID is still recorded alongside the resolved target
    result = neo4j_session.run(
        """
        MATCH (r:CloudflareRulesetRule)
        WHERE r.executed_ruleset_id IS NOT NULL
        RETURN r.id AS id,
               r.executed_ruleset_id AS ruleset_id,
               r.executed_deployment_id AS deployment_id
        """
    )
    assert {
        (record["id"], record["ruleset_id"], record["deployment_id"])
        for record in result
    } == {
        (
            f"{ACCOUNT_WAF_DEPLOYMENT}/{ACCOUNT_EXECUTE_RULE_ID}",
            MANAGED_RULESET_ID,
            ACCOUNT_MANAGED_DEPLOYMENT,
        ),
        (
            f"{ZONE_FIREWALL_DEPLOYMENT}/{ZONE_EXECUTE_RULE_ID}",
            MANAGED_RULESET_ID,
            ZONE_MANAGED_DEPLOYMENT,
        ),
    }

    # Assert the rate limit is captured
    result = neo4j_session.run(
        """
        MATCH (r:CloudflareRulesetRule)
        WHERE r.ratelimit_period IS NOT NULL
        RETURN r.id AS id,
               r.ratelimit_period AS period,
               r.ratelimit_requests_per_period AS requests
        """
    )
    assert [dict(record) for record in result] == [
        {
            "id": f"{ZONE_FIREWALL_DEPLOYMENT}/{CHALLENGE_RULE_ID}",
            "period": 60,
            "requests": 10,
        },
    ]


@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_ruleset_rules",
    side_effect=_fake_ruleset_rules,
)
@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_rulesets",
    side_effect=_fake_rulesets,
)
@patch("cloudflare.Cloudflare")
def test_cloudflare_rulesets_ontology_label_is_scoped_to_security_phases(
    mock_cloudflare, mock_rulesets, mock_rules, neo4j_session
):
    """
    Ensure that only the access-control rulesets carry the NetworkAccessControl
    label, so cache and transform rulesets stay out of firewall queries
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.rulesets.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert: the cache ruleset is absent. Scoped to this account, since other
    # tests in this module leave deployments of a second account behind.
    result = neo4j_session.run(
        """
        MATCH (:CloudflareAccount {id: $account_id})-[:RESOURCE]->
              (r:CloudflareRuleset:NetworkAccessControl)
        RETURN r.id AS id, r._ont_name AS name
        """,
        account_id=ACCOUNT_ID,
    )
    assert {(record["id"], record["name"]) for record in result} == {
        (ACCOUNT_WAF_DEPLOYMENT, "Springfield account WAF"),
        (ACCOUNT_MANAGED_DEPLOYMENT, "Cloudflare Managed Ruleset"),
        (ZONE_FIREWALL_DEPLOYMENT, "Simpson custom firewall"),
        (ZONE_MANAGED_DEPLOYMENT, "Cloudflare Managed Ruleset"),
    }


@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_ruleset_rules",
    side_effect=_fake_ruleset_rules,
)
@patch.object(
    cartography.intel.cloudflare.rulesets,
    "get_rulesets",
    side_effect=_fake_rulesets,
)
@patch("cloudflare.Cloudflare")
def test_shared_managed_ruleset_does_not_merge_scopes_or_accounts(
    mock_cloudflare, mock_rulesets, mock_rules, neo4j_session
):
    """
    Ensure that the Cloudflare Managed Ruleset, whose API ID is the same in every
    scope and every account, produces one node per deployment instead of a single
    node whose scope flips and whose edges span tenants
    """

    # Arrange: two accounts, each with one zone, both deploying the same managed
    # ruleset at the account level and at the zone level
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    cartography.intel.cloudflare.accounts.load_accounts(
        neo4j_session,
        [OTHER_ACCOUNT],
        TEST_UPDATE_TAG,
    )
    cartography.intel.cloudflare.zones.load_zones(
        neo4j_session,
        [OTHER_ZONE],
        OTHER_ACCOUNT["id"],
        TEST_UPDATE_TAG,
    )

    # Act
    for account_id, zone in (
        (ACCOUNT_ID, tests.data.cloudflare.zones.CLOUDFLARE_ZONES[0]),
        (OTHER_ACCOUNT["id"], OTHER_ZONE),
    ):
        cartography.intel.cloudflare.rulesets.sync(
            neo4j_session,
            mock_cloudflare,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "account_id": account_id},
            account_id,
            [zone],
        )

    # Assert the managed ruleset yields four distinct deployments, each keeping
    # its own scope rather than the last one written
    result = neo4j_session.run(
        """
        MATCH (r:CloudflareRuleset {ruleset_id: $ruleset_id})
        RETURN r.id AS id, r.scope AS scope
        """,
        ruleset_id=MANAGED_RULESET_ID,
    )
    assert {(record["id"], record["scope"]) for record in result} == {
        (ACCOUNT_MANAGED_DEPLOYMENT, "account"),
        (ZONE_MANAGED_DEPLOYMENT, "zone"),
        (f"{OTHER_ACCOUNT['id']}/{MANAGED_RULESET_ID}", "account"),
        (f"{OTHER_ZONE['id']}/{MANAGED_RULESET_ID}", "zone"),
    }

    # Assert no deployment is owned by more than one account
    result = neo4j_session.run(
        """
        MATCH (a:CloudflareAccount)-[:RESOURCE]->(r:CloudflareRuleset)
        WITH r, collect(DISTINCT a.id) AS accounts
        WHERE size(accounts) > 1
        RETURN r.id AS id, accounts
        """
    )
    assert [dict(record) for record in result] == []

    # Assert no deployment is attached to a zone of another account
    result = neo4j_session.run(
        """
        MATCH (z:CloudflareZone)-[:HAS_RULESET]->(r:CloudflareRuleset)
        MATCH (a:CloudflareAccount)-[:RESOURCE]->(r)
        MATCH (za:CloudflareAccount)-[:RESOURCE]->(z)
        WHERE za.id <> a.id
        RETURN r.id AS id, z.id AS zone_id
        """
    )
    assert [dict(record) for record in result] == []

    # Assert every `execute` rule turns on exactly one deployment, and never one
    # belonging to another account
    result = neo4j_session.run(
        """
        MATCH (rule:CloudflareRulesetRule)
        WHERE rule.executed_ruleset_id IS NOT NULL
        MATCH (rule)-[:EXECUTES]->(target:CloudflareRuleset)
        WITH rule, collect(DISTINCT target) AS targets
        WHERE size(targets) > 1
        RETURN rule.id AS id
        """
    )
    assert [dict(record) for record in result] == []

    result = neo4j_session.run(
        """
        MATCH (a:CloudflareAccount)-[:RESOURCE]->(rule:CloudflareRulesetRule)
        MATCH (rule)-[:EXECUTES]->(target:CloudflareRuleset)
        MATCH (ta:CloudflareAccount)-[:RESOURCE]->(target)
        WHERE ta.id <> a.id
        RETURN rule.id AS id, target.id AS target_id
        """
    )
    assert [dict(record) for record in result] == []
