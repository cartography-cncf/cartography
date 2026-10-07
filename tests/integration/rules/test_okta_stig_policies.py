"""Integration tests for the Okta STIG rules that read policy, zone, token, and
log stream data. The graph is seeded with the property names the Okta models
define, so each Fact's main, visual, and count queries run against Neo4j."""

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules import okta_stig
from cartography.rules.spec.model import Rule

ORG_A = "synthetic-org-a"
ORG_B = "synthetic-org-b"

# Org A is compliant with nothing; org B is compliant with everything. Each
# entity's id says which way it should evaluate.
SEED = """
// Org A's token could read log streams and admin roles; org B's could only read
// log streams, so org B's API tokens are not evaluated for super admin owners.
CREATE (a:OktaOrganization {
    id: $org_a,
    lastupdated: 1,
    log_streams_synced: true,
    admin_roles_synced: true,
    admin_console_session_idle_timeout_minutes: 60,
    admin_console_session_max_lifetime_minutes: 720
})
CREATE (b:OktaOrganization {
    id: $org_b,
    lastupdated: 1,
    log_streams_synced: true,
    admin_roles_synced: false,
    admin_console_session_idle_timeout_minutes: 15,
    admin_console_session_max_lifetime_minutes: 720
})

// Global session policies
CREATE (a)-[:RESOURCE]->(gs_a:OktaPolicy {
    id: 'gs-weak', type: 'OKTA_SIGN_ON', status: 'ACTIVE', name: 'Default Policy'
})
CREATE (gs_a)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'gs-weak-top', status: 'ACTIVE', priority: 1, name: 'Default Rule',
    session_max_idle_minutes: 120, session_max_lifetime_minutes: 0,
    session_use_persistent_cookie: true, network_connection: 'ANYWHERE'
})
CREATE (b)-[:RESOURCE]->(gs_b:OktaPolicy {
    id: 'gs-strong', type: 'OKTA_SIGN_ON', status: 'ACTIVE', name: 'Default Policy'
})
CREATE (gs_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'gs-strong-top', status: 'ACTIVE', priority: 1, name: 'STIG',
    session_max_idle_minutes: 15, session_max_lifetime_minutes: 1080,
    session_use_persistent_cookie: false, network_connection: 'ZONE'
})
// A lax lower-priority rule does not change the result.
CREATE (gs_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'gs-strong-default', status: 'ACTIVE', priority: 2, name: 'Default Rule',
    session_max_idle_minutes: 120, session_max_lifetime_minutes: 0,
    session_use_persistent_cookie: true, network_connection: 'ANYWHERE'
})
// Inactive higher-priority rules are skipped.
CREATE (gs_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'gs-strong-inactive', status: 'INACTIVE', priority: 0,
    session_max_idle_minutes: 999, session_max_lifetime_minutes: 0,
    session_use_persistent_cookie: true
})

// Admin Console and Dashboard authentication policies
CREATE (a)-[:RESOURCE]->(ac_a:OktaPolicy {
    id: 'admin-weak', type: 'ACCESS_POLICY', status: 'ACTIVE',
    name: 'Renamed admin policy', first_party_app_names: ['saasure']
})
CREATE (ac_a)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'admin-weak-top', status: 'ACTIVE', priority: 0, access: 'ALLOW',
    factor_mode: '1FA', phishing_resistant_required: false
})
CREATE (a)-[:RESOURCE]->(db_a:OktaPolicy {
    id: 'dashboard-weak', type: 'ACCESS_POLICY', status: 'ACTIVE',
    name: 'Okta Dashboard Policy', first_party_app_names: []
})
CREATE (db_a)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'dashboard-weak-top', status: 'ACTIVE', priority: 0, access: 'ALLOW',
    factor_mode: '1FA', phishing_resistant_required: false
})
CREATE (b)-[:RESOURCE]->(ac_b:OktaPolicy {
    id: 'admin-strong', type: 'ACCESS_POLICY', status: 'ACTIVE',
    name: 'Okta Admin Console', first_party_app_names: ['saasure']
})
// A higher-priority deny rule is not the rule that grants access.
CREATE (ac_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'admin-strong-deny', status: 'ACTIVE', priority: 0, access: 'DENY',
    factor_mode: '1FA', phishing_resistant_required: false
})
CREATE (ac_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'admin-strong-top', status: 'ACTIVE', priority: 1, access: 'ALLOW',
    factor_mode: '2FA', phishing_resistant_required: true
})
CREATE (b)-[:RESOURCE]->(db_b:OktaPolicy {
    id: 'dashboard-strong', type: 'ACCESS_POLICY', status: 'ACTIVE',
    name: 'Custom name', first_party_app_names: ['okta_enduser']
})
CREATE (db_b)-[:HAS_RULE]->(:OktaPolicyRule {
    id: 'dashboard-strong-top', status: 'ACTIVE', priority: 0, access: 'ALLOW',
    factor_mode: '2FA', phishing_resistant_required: true,
    network_connection: 'ZONE'
})
// A policy named like the preset but assigned to another first-party app.
CREATE (b)-[:RESOURCE]->(:OktaPolicy {
    id: 'not-dashboard', type: 'ACCESS_POLICY', status: 'ACTIVE',
    name: 'Okta Dashboard', first_party_app_names: ['okta_browser_plugin']
})

// Applications
CREATE (a)-[:RESOURCE]->(app_a:OktaApplication {id: 'app-no-zone', status: 'ACTIVE'})
CREATE (a)-[:RESOURCE]->(app_inactive:OktaApplication {
    id: 'app-inactive', status: 'INACTIVE'
})
CREATE (ac_a)-[:APPLIES_TO]->(app_a)
CREATE (ac_a)-[:APPLIES_TO]->(app_inactive)
CREATE (b)-[:RESOURCE]->(app_b:OktaApplication {id: 'app-with-zone', status: 'ACTIVE'})
CREATE (db_b)-[:APPLIES_TO]->(app_b)

// Password policies
CREATE (a)-[:RESOURCE]->(:OktaPolicy {
    id: 'pw-weak', type: 'PASSWORD', status: 'ACTIVE', auth_provider: 'OKTA',
    password_min_length: 8, password_min_lowercase: 0, password_min_uppercase: 0,
    password_min_number: 0, password_min_symbol: 0,
    password_common_password_check: false, password_min_age_minutes: 0,
    password_max_age_days: 0, password_history_count: 0, lockout_max_attempts: 10
})
CREATE (a)-[:RESOURCE]->(:OktaPolicy {
    id: 'pw-directory', type: 'PASSWORD', status: 'ACTIVE',
    auth_provider: 'ACTIVE_DIRECTORY', password_min_length: 4
})
CREATE (a)-[:RESOURCE]->(:OktaPolicy {
    id: 'pw-inactive', type: 'PASSWORD', status: 'INACTIVE', auth_provider: 'OKTA',
    password_min_length: 4
})
CREATE (b)-[:RESOURCE]->(:OktaPolicy {
    id: 'pw-strong', type: 'PASSWORD', status: 'ACTIVE', auth_provider: 'OKTA',
    password_min_length: 15, password_min_lowercase: 1, password_min_uppercase: 1,
    password_min_number: 1, password_min_symbol: 1,
    password_common_password_check: true, password_min_age_minutes: 1440,
    password_max_age_days: 60, password_history_count: 5, lockout_max_attempts: 3
})

// Log streams
CREATE (a)-[:RESOURCE]->(:OktaLogStream {id: 'stream-inactive', status: 'INACTIVE'})
CREATE (b)-[:RESOURCE]->(:OktaLogStream {id: 'stream-active', status: 'ACTIVE'})

// Network zones
CREATE (a)-[:RESOURCE]->(:OktaNetworkZone {
    id: 'zone-a-legacy', type: 'IP', usage: 'POLICY', status: 'ACTIVE', gateways: []
})
CREATE (a)-[:RESOURCE]->(:OktaNetworkZone {
    id: 'zone-a-enhanced', type: 'DYNAMIC_V2', usage: 'BLOCKLIST',
    status: 'INACTIVE', ip_service_categories_include: ['ALL_ANONYMIZERS']
})
CREATE (a)-[:RESOURCE]->(:OktaNetworkZone {
    id: 'zone-a-empty-blocklist', type: 'IP', usage: 'BLOCKLIST', status: 'ACTIVE',
    gateways: []
})
CREATE (b)-[:RESOURCE]->(:OktaNetworkZone {
    id: 'zone-b-enhanced', type: 'DYNAMIC_V2', usage: 'BLOCKLIST',
    status: 'ACTIVE', ip_service_categories_include: ['ALL_ANONYMIZERS']
})
// An org whose zones were not synced is not evaluated.
CREATE (:OktaOrganization {id: 'synthetic-org-unsynced'})
// The token could not read log streams in the org's latest sync.
CREATE (:OktaOrganization {
    id: 'synthetic-org-stale-coverage', lastupdated: 2, log_streams_synced: false
})

// API tokens and their owners
CREATE (a)-[:RESOURCE]->(super:OktaUser {id: 'u-super', login: 'super@example.invalid'})
CREATE (a)-[:RESOURCE]->(grp_super:OktaUser {
    id: 'u-group-super', login: 'group@example.invalid'
})
CREATE (b)-[:RESOURCE]->(svc:OktaUser {id: 'u-service', login: 'svc@example.invalid'})
CREATE (super)-[:HAS_ROLE]->(:OktaUserRole {id: 'role-super', role_type: 'SUPER_ADMIN'})
CREATE (grp_super)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup {id: 'g-admins'})
    -[:HAS_ROLE]->(:OktaGroupRole {id: 'grole-super', role_type: 'SUPER_ADMIN'})
CREATE (svc)-[:HAS_ROLE]->(:OktaUserRole {id: 'role-readonly', role_type: 'READ_ONLY_ADMIN'})
CREATE (a)-[:RESOURCE]->(t1:OktaApiToken {
    id: 'token-anywhere-super', name: 'anywhere', network_connection: 'ANYWHERE',
    user_id: 'u-super'
})
CREATE (t1)-[:OWNED_BY]->(super)
CREATE (a)-[:RESOURCE]->(t2:OktaApiToken {
    id: 'token-exclude-only-group-super', name: 'exclude only',
    network_connection: 'ZONE', user_id: 'u-group-super'
})
CREATE (t2)-[:OWNED_BY]->(grp_super)
WITH a, b, t2, svc
MATCH (legacy:OktaNetworkZone {id: 'zone-a-legacy'})
CREATE (t2)-[:BLOCKED_FROM]->(legacy)
CREATE (a)-[:RESOURCE]->(:OktaApiToken {id: 'token-no-network', name: 'legacy'})
CREATE (b)-[:RESOURCE]->(t3:OktaApiToken {
    id: 'token-zoned-service', name: 'zoned', network_connection: 'ZONE',
    user_id: 'u-service'
})
CREATE (t3)-[:OWNED_BY]->(svc)
CREATE (t3)-[:ALLOWED_FROM]->(:OktaNetworkZone {id: 'zone-b-corp'})
"""

# rule -> (asset ids expected in findings, expected count query result)
EXPECTED: dict[str, tuple[set[str], int]] = {
    "okta_global_session_idle_timeout_too_long": ({"gs-weak"}, 2),
    "okta_global_session_lifetime_too_long": ({"gs-weak"}, 2),
    "okta_global_session_persistent_cookies": ({"gs-weak"}, 2),
    "okta_global_session_without_network_zones": ({"gs-weak"}, 2),
    "okta_admin_console_idle_timeout_too_long": ({ORG_A}, 2),
    "okta_dashboard_phishing_resistant_not_required": ({"dashboard-weak"}, 2),
    "okta_admin_console_phishing_resistant_not_required": ({"admin-weak"}, 2),
    "okta_admin_console_mfa_not_required": ({"admin-weak"}, 2),
    "okta_dashboard_mfa_not_required": ({"dashboard-weak"}, 2),
    "okta_password_lockout_threshold_too_high": ({"pw-weak"}, 2),
    "okta_password_min_length_too_short": ({"pw-weak"}, 2),
    "okta_password_uppercase_not_required": ({"pw-weak"}, 2),
    "okta_password_lowercase_not_required": ({"pw-weak"}, 2),
    "okta_password_number_not_required": ({"pw-weak"}, 2),
    "okta_password_symbol_not_required": ({"pw-weak"}, 2),
    "okta_password_min_age_too_short": ({"pw-weak"}, 2),
    "okta_password_max_age_too_long": ({"pw-weak"}, 2),
    "okta_password_common_password_check_disabled": ({"pw-weak"}, 2),
    "okta_password_history_too_short": ({"pw-weak"}, 2),
    "okta_system_log_not_streamed": ({ORG_A}, 2),
    "okta_api_token_without_network_zone": (
        {"token-anywhere-super", "token-exclude-only-group-super", "token-no-network"},
        4,
    ),
    "okta_api_token_owned_by_super_admin": (
        {"token-anywhere-super", "token-exclude-only-group-super"},
        3,
    ),
    "okta_anonymizer_blocklist_missing": ({ORG_A}, 2),
    "okta_app_policy_without_network_zones": ({"admin-weak"}, 2),
}


def _run_query(neo4j_session, query: str) -> list[dict]:
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def test_okta_stig_policy_rules(neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(SEED, org_a=ORG_A, org_b=ORG_B)
    rules = {
        value.id: value for value in vars(okta_stig).values() if isinstance(value, Rule)
    }

    for rule_id, (expected_assets, expected_count) in EXPECTED.items():
        rule = rules[rule_id]
        fact = rule.facts[0]

        # Act
        findings = _run_query(neo4j_session, fact.cypher_query)
        visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
        count = _run_query(neo4j_session, fact.cypher_count_query)[0]["count"]
        parsed = rule.parse_results(fact, findings)

        # Assert
        assert {
            row[fact.asset_id_field] for row in findings
        } == expected_assets, rule_id
        assert count == expected_count, rule_id
        assert bool(visual_rows) == bool(expected_assets), rule_id
        assert len(parsed) == len(findings), rule_id


def test_expected_table_covers_every_phase_three_rule() -> None:
    rule_ids = {
        value.id for value in vars(okta_stig).values() if isinstance(value, Rule)
    }
    phase_one = {
        "okta_inactive_users_not_disabled",
        "okta_verify_fips_compliance_not_required",
    }
    assert set(EXPECTED) == rule_ids - phase_one
