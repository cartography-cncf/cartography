"""Integration tests for the Okta facts on admin privileges, service apps, and MFA
enrollment. The graph is seeded with the property names the Okta models define,
so each Fact's main, visual, and count queries run against Neo4j."""

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules import RULES

# Org A's credential could read admin roles, app roles, and app grants. Org B's
# could read app roles only, so nothing that needs user or group roles or app
# grants is evaluated there. Each entity's id says how it should evaluate.
SEED = """
CREATE (a:OktaOrganization {
    id: 'org-a',
    admin_roles_synced: true,
    application_roles_synced: true,
    app_grants_synced: true
})
CREATE (b:OktaOrganization {
    id: 'org-b',
    admin_roles_synced: false,
    application_roles_synced: true,
    app_grants_synced: false
})

// OAuth service apps
CREATE (a)-[:RESOURCE]->(write:OktaApplication {
    id: 'svc-super-users-manage', label: 'Provisioning', status: 'ACTIVE',
    settings_oauth_client_application_type: 'service',
    credentials_oauth_client_token_endpoint_auth_method: 'private_key_jwt',
    settings_oauth_client_dpop_bound_access_tokens: true,
    granted_scopes: ['okta.apps.read', 'okta.users.manage']
})
CREATE (write)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-super-users-manage:ra1', role_type: 'SUPER_ADMIN',
    label: 'Super Administrator', status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(readonly:OktaApplication {
    id: 'svc-super-read-only-no-dpop', label: 'Inventory', status: 'ACTIVE',
    settings_oauth_client_application_type: 'service',
    settings_oauth_client_dpop_bound_access_tokens: false,
    granted_scopes: ['okta.users.read']
})
CREATE (readonly)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-super-read-only-no-dpop:ra1', role_type: 'SUPER_ADMIN',
    status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(apps:OktaApplication {
    id: 'svc-app-admin-apps-manage-dpop-unset', label: 'App deployer',
    status: 'ACTIVE', settings_oauth_client_application_type: 'service',
    granted_scopes: ['okta.apps.manage']
})
CREATE (apps)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-app-admin-apps-manage-dpop-unset:ra1', role_type: 'APP_ADMIN',
    status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(inactive:OktaApplication {
    id: 'svc-inactive-app', status: 'INACTIVE',
    settings_oauth_client_application_type: 'service',
    settings_oauth_client_dpop_bound_access_tokens: false,
    granted_scopes: ['okta.users.manage']
})
CREATE (inactive)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-inactive-app:ra1', role_type: 'SUPER_ADMIN', status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(revoked:OktaApplication {
    id: 'svc-inactive-role', status: 'ACTIVE',
    settings_oauth_client_application_type: 'service',
    settings_oauth_client_dpop_bound_access_tokens: false,
    granted_scopes: ['okta.users.manage']
})
CREATE (revoked)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-inactive-role:ra1', role_type: 'SUPER_ADMIN', status: 'INACTIVE'
})
CREATE (a)-[:RESOURCE]->(:OktaApplication {
    id: 'svc-no-role', status: 'ACTIVE',
    settings_oauth_client_application_type: 'service',
    settings_oauth_client_dpop_bound_access_tokens: false,
    granted_scopes: ['okta.users.manage']
})
CREATE (a)-[:RESOURCE]->(:OktaApplication {
    id: 'web-app', status: 'ACTIVE', settings_oauth_client_application_type: 'web',
    granted_scopes: []
})
CREATE (b)-[:RESOURCE]->(org_b_app:OktaApplication {
    id: 'svc-org-b-grants-unknown-no-dpop', status: 'ACTIVE',
    settings_oauth_client_application_type: 'service',
    settings_oauth_client_dpop_bound_access_tokens: false
})
CREATE (org_b_app)-[:HAS_ROLE]->(:OktaApplicationRole {
    id: 'svc-org-b-grants-unknown-no-dpop:ra1', role_type: 'SUPER_ADMIN',
    status: 'ACTIVE'
})

// Users, their roles, and their factors
CREATE (a)-[:RESOURCE]->(super:OktaUser {
    id: 'u-super-admin-with-push', login: 'super@example.invalid', status: 'ACTIVE'
})
CREATE (super)-[:HAS_ROLE]->(:OktaUserRole {
    id: 'ra-super', role_type: 'SUPER_ADMIN', label: 'Super Administrator',
    status: 'ACTIVE'
})
CREATE (super)-[:FACTOR]->(:OktaUserFactor {
    id: 'f-push', factor_type: 'push', status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(helpdesk:OktaUser {
    id: 'u-help-desk-admin-question-only', status: 'ACTIVE'
})
CREATE (helpdesk)-[:HAS_ROLE]->(:OktaUserRole {
    id: 'ra-help-desk', role_type: 'HELP_DESK_ADMIN'
})
CREATE (helpdesk)-[:FACTOR]->(:OktaUserFactor {
    id: 'f-question', factor_type: 'question', status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(readonly_admin:OktaUser {
    id: 'u-read-only-admin-pending-factor', status: 'ACTIVE'
})
CREATE (readonly_admin)-[:HAS_ROLE]->(:OktaUserRole {
    id: 'ra-read-only', role_type: 'READ_ONLY_ADMIN', status: 'ACTIVE'
})
CREATE (readonly_admin)-[:FACTOR]->(:OktaUserFactor {
    id: 'f-webauthn-pending', factor_type: 'webauthn',
    status: 'PENDING_ACTIVATION'
})
CREATE (a)-[:RESOURCE]->(gone:OktaUser {
    id: 'u-deprovisioned-super-admin', status: 'DEPROVISIONED'
})
CREATE (gone)-[:HAS_ROLE]->(:OktaUserRole {
    id: 'ra-gone', role_type: 'SUPER_ADMIN', status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(:OktaUser {id: 'u-locked-out-no-factor', status: 'LOCKED_OUT'})
CREATE (b)-[:RESOURCE]->(org_b_user:OktaUser {
    id: 'u-org-b-super-admin-with-sms', status: 'ACTIVE'
})
CREATE (org_b_user)-[:HAS_ROLE]->(:OktaUserRole {
    id: 'ra-org-b', role_type: 'SUPER_ADMIN', status: 'ACTIVE'
})
CREATE (org_b_user)-[:FACTOR]->(:OktaUserFactor {
    id: 'f-sms', factor_type: 'sms', status: 'ACTIVE'
})

// Groups and their roles
CREATE (a)-[:RESOURCE]->(org_admins:OktaGroup {id: 'g-org-admins', name: 'Org admins'})
CREATE (org_admins)-[:HAS_ROLE]->(:OktaGroupRole {
    id: 'gra-org-admin', role_type: 'ORG_ADMIN', label: 'Organization Administrator',
    status: 'ACTIVE'
})
CREATE (a)-[:RESOURCE]->(reporters:OktaGroup {id: 'g-report-admins'})
CREATE (reporters)-[:HAS_ROLE]->(:OktaGroupRole {
    id: 'gra-report', role_type: 'REPORT_ADMIN', status: 'ACTIVE'
})
CREATE (b)-[:RESOURCE]->(org_b_group:OktaGroup {id: 'g-org-b-super-admins'})
CREATE (org_b_group)-[:HAS_ROLE]->(:OktaGroupRole {
    id: 'gra-org-b', role_type: 'SUPER_ADMIN', status: 'ACTIVE'
})
"""

# (rule id, fact id) -> (asset ids expected in findings, expected count result)
EXPECTED: dict[tuple[str, str], tuple[set[str], int]] = {
    (
        "okta_service_app_admin_write_access",
        "okta_service_app_admin_role_with_manage_scope",
    ): (
        {"svc-super-users-manage", "svc-app-admin-apps-manage-dpop-unset"},
        # Active service apps in org A, the only org with grants synced.
        5,
    ),
    (
        "okta_admin_service_app_without_dpop",
        "okta_admin_service_app_dpop_not_required",
    ): (
        {
            "svc-super-read-only-no-dpop",
            "svc-app-admin-apps-manage-dpop-unset",
            "svc-org-b-grants-unknown-no-dpop",
        },
        6,
    ),
    ("identity_administration_privileges", "okta_user_identity_admin_roles"): (
        {"u-super-admin-with-push", "u-help-desk-admin-question-only"},
        5,
    ),
    ("identity_administration_privileges", "okta_group_identity_admin_roles"): (
        {"g-org-admins"},
        2,
    ),
    ("identity_administration_privileges", "okta_application_identity_admin_roles"): (
        # A role alone is not enough: the app also needs a scope that writes
        # identities, and an active role assignment.
        {"svc-super-users-manage"},
        7,
    ),
    ("identity_mfa_gaps", "okta_user_mfa_not_enrolled"): (
        {
            "u-help-desk-admin-question-only",
            "u-read-only-admin-pending-factor",
            "u-locked-out-no-factor",
        },
        # Users who can sign in, in every org: MFA enrollment needs no roles.
        5,
    ),
}


def _run_query(neo4j_session, query: str) -> list[dict]:
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def test_okta_privilege_facts(neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(SEED)

    for (rule_id, fact_id), (expected_assets, expected_count) in EXPECTED.items():
        rule = RULES[rule_id]
        fact = rule.get_fact_by_id(fact_id)
        assert fact is not None, fact_id

        # Act
        findings = _run_query(neo4j_session, fact.cypher_query)
        visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
        count = _run_query(neo4j_session, fact.cypher_count_query)[0]["count"]
        parsed = rule.parse_results(fact, findings)

        # Assert
        assert {
            row[fact.asset_id_field] for row in findings
        } == expected_assets, fact_id
        assert count == expected_count, fact_id
        assert bool(visual_rows) == bool(expected_assets), fact_id
        assert len(parsed) == len(findings), fact_id


def test_service_app_findings_report_role_and_write_scopes(neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(SEED)
    rule = RULES["okta_service_app_admin_write_access"]
    fact = rule.facts[0]

    # Act
    parsed = rule.parse_results(fact, _run_query(neo4j_session, fact.cypher_query))

    # Assert
    finding = next(f for f in parsed if f.app_id == "svc-super-users-manage")
    assert finding.app_name == "Provisioning"
    assert finding.org_id == "org-a"
    assert finding.role_types == ["SUPER_ADMIN"]
    assert finding.write_scopes == ["okta.users.manage"]
    assert finding.token_endpoint_auth_method == "private_key_jwt"
    assert finding.dpop_required is True
