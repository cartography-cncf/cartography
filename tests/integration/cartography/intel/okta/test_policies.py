import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.policies
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.policies import FIRST_PARTY_APPS
from tests.data.okta.policies import MAPPINGS_BY_POLICY
from tests.data.okta.policies import POLICIES_BY_TYPE
from tests.data.okta.policies import RULES_BY_POLICY
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


async def _fake_collect_raw_paginated(okta_client, path, params=None):
    if path == "/api/v1/policies":
        return POLICIES_BY_TYPE[params["type"]]
    policy_id, resource = path.removeprefix("/api/v1/policies/").split("/")
    if resource == "rules":
        return RULES_BY_POLICY[policy_id]
    return MAPPINGS_BY_POLICY.get(policy_id, [])


async def _fake_get_raw_json(okta_client, path):
    return FIRST_PARTY_APPS[path.removeprefix("/api/v1/apps/")]


def _nodes(neo4j_session, label: str, fields: list[str]) -> set[tuple]:
    nodes = check_nodes(neo4j_session, label, fields)
    assert nodes is not None
    return nodes


def _seed_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        FOREACH (app_id IN ['0oa-slack', '0oa-github'] |
            MERGE (org)-[:RESOURCE]->(:OktaApplication {id: app_id, lastupdated: $update_tag})
        )
        FOREACH (group_id IN ['00g-everyone', '00g-admins', '00g-contractors'] |
            MERGE (org)-[:RESOURCE]->(:OktaGroup {id: group_id, lastupdated: $update_tag})
        )
        MERGE (org)-[:RESOURCE]->(:OktaUser {id: '00u-breakglass', lastupdated: $update_tag})
        MERGE (org)-[:RESOURCE]->(stale:OktaPolicy {id: 'stale-policy'})
        SET stale.lastupdated = 1
        MERGE (stale)-[:HAS_RULE]->(stale_rule:OktaPolicyRule {id: 'stale-rule'})
        SET stale_rule.lastupdated = 1
        MERGE (org)-[:RESOURCE]->(stale_rule)
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.okta.policies,
    "get_raw_json",
    side_effect=_fake_get_raw_json,
)
@patch.object(
    cartography.intel.okta.policies,
    "collect_raw_paginated",
    side_effect=_fake_collect_raw_paginated,
)
def test_sync_okta_policies(mock_collect, mock_get_raw_json, neo4j_session) -> None:
    # Arrange
    _seed_graph(neo4j_session)

    # Act
    cartography.intel.okta.policies.sync_okta_policies(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert: policies and their STIG-relevant settings
    assert check_nodes(
        neo4j_session,
        "OktaPolicy",
        ["id", "type", "name", "priority"],
    ) == {
        ("00p-global-session", "OKTA_SIGN_ON", "Default Policy", 1),
        ("00p-password-default", "PASSWORD", "Default Policy", 2),
        ("00p-password-legacy", "PASSWORD", "Legacy Contractors", 1),
        ("00p-enrollment", "MFA_ENROLL", "Default Policy", 1),
        ("rst-admin-console", "ACCESS_POLICY", "Okta Admin Console", 1),
        ("rst-dashboard", "ACCESS_POLICY", "Okta Dashboard", 1),
        ("rst-default", "ACCESS_POLICY", "Default Policy", 1),
        ("rst-profile-enrollment", "PROFILE_ENROLLMENT", "Default Policy", 1),
    }
    assert _nodes(
        neo4j_session,
        "OktaPolicy",
        [
            "id",
            "password_min_length",
            "password_min_symbol",
            "password_common_password_check",
            "password_min_age_minutes",
            "password_max_age_days",
            "password_history_count",
            "lockout_max_attempts",
        ],
    ) >= {
        ("00p-password-default", 15, 1, True, 1440, 60, 5, 3),
        ("00p-password-legacy", 8, 0, None, 0, 0, 0, 10),
    }
    first_party = {
        row["id"]: row["names"]
        for row in neo4j_session.run(
            """
            MATCH (p:OktaPolicy {type: 'ACCESS_POLICY'})
            RETURN p.id AS id, p.first_party_app_names AS names
            """,
        )
    }
    assert first_party == {
        "rst-admin-console": ["saasure"],
        "rst-dashboard": ["okta_enduser"],
        "rst-default": [],
    }
    # Only apps without an OktaApplication node are fetched individually.
    assert sorted(call.args[1] for call in mock_get_raw_json.call_args_list) == [
        "/api/v1/apps/0oa-admin-console",
        "/api/v1/apps/0oa-dashboard",
    ]

    # Assert: rules
    assert _nodes(
        neo4j_session,
        "OktaPolicyRule",
        [
            "id",
            "session_max_idle_minutes",
            "session_max_lifetime_minutes",
            "session_use_persistent_cookie",
        ],
    ) >= {
        ("0pr-session-hardened", 15, 1080, False),
        ("0pr-session-default", 120, 0, True),
    }
    assert _nodes(
        neo4j_session,
        "OktaPolicyRule",
        ["id", "access", "factor_mode", "phishing_resistant_required"],
    ) >= {
        ("rul-admin-phishing-resistant", "ALLOW", "2FA", True),
        ("rul-admin-catch-all", "DENY", "1FA", False),
        ("rul-dashboard-one-factor", "ALLOW", "1FA", False),
        ("rul-default-mixed", "ALLOW", "2FA", False),
    }
    assert {
        record["id"]
        for record in neo4j_session.run("MATCH (r:OktaPolicyRule) RETURN r.id AS id")
    } == {
        "0pr-session-hardened",
        "0pr-session-default",
        "0pr-password-default",
        "0pr-enrollment-default",
        "rul-admin-phishing-resistant",
        "rul-admin-catch-all",
        "rul-dashboard-one-factor",
        "rul-default-mixed",
        "rul-profile-enrollment",
    }

    # Assert: relationships
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaPolicy",
        "id",
        "RESOURCE",
    ) == {
        (TEST_ORG_ID, policy_id)
        for policy_id in (
            "00p-global-session",
            "00p-password-default",
            "00p-password-legacy",
            "00p-enrollment",
            "rst-admin-console",
            "rst-dashboard",
            "rst-default",
            "rst-profile-enrollment",
        )
    }
    assert check_rels(
        neo4j_session,
        "OktaPolicy",
        "id",
        "OktaPolicyRule",
        "id",
        "HAS_RULE",
    ) >= {
        ("00p-global-session", "0pr-session-hardened"),
        ("00p-global-session", "0pr-session-default"),
        ("rst-admin-console", "rul-admin-phishing-resistant"),
        ("rst-admin-console", "rul-admin-catch-all"),
    }
    assert check_rels(
        neo4j_session,
        "OktaPolicy",
        "id",
        "OktaApplication",
        "id",
        "APPLIES_TO",
    ) == {("rst-default", "0oa-slack"), ("rst-default", "0oa-github")}
    assert check_rels(
        neo4j_session,
        "OktaPolicy",
        "id",
        "OktaGroup",
        "id",
        "EXCLUDES",
    ) == {("00p-password-legacy", "00g-admins")}
    assert ("00p-password-legacy", "00g-contractors") in check_rels(
        neo4j_session,
        "OktaPolicy",
        "id",
        "OktaGroup",
        "id",
        "APPLIES_TO",
    )
    assert check_rels(
        neo4j_session,
        "OktaPolicyRule",
        "id",
        "OktaGroup",
        "id",
        "APPLIES_TO",
    ) == {
        ("rul-admin-phishing-resistant", "00g-admins"),
        ("rul-dashboard-one-factor", "00g-everyone"),
    }
    assert check_rels(
        neo4j_session,
        "OktaPolicyRule",
        "id",
        "OktaUser",
        "id",
        "EXCLUDES",
    ) == {("0pr-session-hardened", "00u-breakglass")}
    zone_conditions = {
        record["id"]: (record["include"], record["exclude"])
        for record in neo4j_session.run(
            """
            MATCH (r:OktaPolicyRule)
            WHERE r.id IN ['0pr-session-hardened', 'rul-admin-phishing-resistant']
            RETURN r.id AS id, r.network_include_zone_ids AS include,
                   r.network_exclude_zone_ids AS exclude
            """,
        )
    }
    assert zone_conditions == {
        "0pr-session-hardened": (["nzo-corp"], []),
        "rul-admin-phishing-resistant": ([], ["nzo-blocklist"]),
    }
    # Assert: raw JSON is kept for fields not modeled as properties
    platform = neo4j_session.run(
        "MATCH (r:OktaPolicyRule {id: 'rul-admin-phishing-resistant'}) "
        "RETURN r.conditions AS conditions",
    ).single()["conditions"]
    assert json.loads(platform)["platform"]["include"][0]["os"]["type"] == "MACOS"

    # Assert: stale nodes are cleaned up
    assert (
        neo4j_session.run(
            "MATCH (n) WHERE n.id IN ['stale-policy', 'stale-rule'] RETURN count(n) AS c",
        ).single()["c"]
        == 0
    )


@patch.object(cartography.intel.okta.policies, "collect_raw_paginated")
def test_sync_okta_policies_skips_when_scope_missing(mock_collect, neo4j_session):
    # Arrange
    _seed_graph(neo4j_session)
    mock_collect.side_effect = OktaApiError(
        "/api/v1/policies",
        SimpleNamespace(error_code="E0000006"),
    )

    # Act
    cartography.intel.okta.policies.sync_okta_policies(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert: nothing loaded and nothing cleaned up
    assert check_nodes(neo4j_session, "OktaPolicy", ["id"]) == {("stale-policy",)}
