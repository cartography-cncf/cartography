from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.intel.googleworkspace.users import load_googleworkspace_users
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_admins_without_enforced_2sv,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_super_admin_accounts_used_for_daily_admin,
)
from cartography.rules.data.rules.nist_ai_rmf import ai_admin_app_authorizations

TEST_CUSTOMER_ID = "synthetic-tenant"
TEST_UPDATE_TAG = 123456789

TEST_USERS = [
    {
        "id": "active-super-admin",
        "primaryEmail": "active-super-admin@example.invalid",
        "name": "Active Super Admin",
        "isAdmin": True,
        "isDelegatedAdmin": False,
        "isEnforcedIn2Sv": True,
        "suspended": False,
        "archived": False,
    },
    {
        "id": "active-delegated-admin",
        "primaryEmail": "active-delegated-admin@example.invalid",
        "name": "Active Delegated Admin",
        "isAdmin": False,
        "isDelegatedAdmin": True,
        "isEnforcedIn2Sv": False,
        "suspended": False,
        "archived": False,
    },
    {
        "id": "active-dual-role-admin",
        "primaryEmail": "active-dual-role-admin@example.invalid",
        "name": "Active Dual Role Admin",
        "isAdmin": True,
        "isDelegatedAdmin": True,
        "isEnforcedIn2Sv": False,
        "suspended": False,
        "archived": False,
    },
    {
        "id": "suspended-dual-role-admin",
        "primaryEmail": "suspended-dual-role-admin@example.invalid",
        "name": "Suspended Dual Role Admin",
        "isAdmin": True,
        "isDelegatedAdmin": True,
        "isEnforcedIn2Sv": False,
        "suspended": True,
        "archived": False,
    },
    {
        "id": "archived-delegated-admin",
        "primaryEmail": "archived-delegated-admin@example.invalid",
        "name": "Archived Delegated Admin",
        "isAdmin": False,
        "isDelegatedAdmin": True,
        "isEnforcedIn2Sv": False,
        "suspended": False,
        "archived": True,
    },
]


def _reset_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")


def _load_test_users(neo4j_session) -> None:
    neo4j_session.run(
        "CREATE (:GoogleWorkspaceTenant {id: $customer_id})",
        customer_id=TEST_CUSTOMER_ID,
    )
    load_googleworkspace_users(
        neo4j_session,
        TEST_USERS,
        TEST_UPDATE_TAG,
        TEST_CUSTOMER_ID,
    )


def _run_query(neo4j_session, query: str) -> list[dict]:
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def _count(neo4j_session, query: str) -> int:
    return _run_query(neo4j_session, query)[0]["count"]


def test_google_workspace_admin_facts_exclude_inactive_accounts(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _load_test_users(neo4j_session)

    admin_2sv_fact = googleworkspace_admins_without_enforced_2sv.facts[0]
    dual_role_fact = googleworkspace_super_admin_accounts_used_for_daily_admin.facts[0]

    # Act
    activity = _run_query(
        neo4j_session,
        """
        MATCH (u:GoogleWorkspaceUser)
        RETURN u.id AS id, u._ont_active AS active
        ORDER BY id
        """,
    )
    admin_2sv_findings = _run_query(neo4j_session, admin_2sv_fact.cypher_query)
    admin_2sv_visual_rows = list(neo4j_session.run(admin_2sv_fact.cypher_visual_query))
    admin_2sv_total = _count(neo4j_session, admin_2sv_fact.cypher_count_query)
    dual_role_findings = _run_query(neo4j_session, dual_role_fact.cypher_query)
    dual_role_visual_rows = list(neo4j_session.run(dual_role_fact.cypher_visual_query))
    dual_role_total = _count(neo4j_session, dual_role_fact.cypher_count_query)

    # Assert
    assert {(row["id"], row["active"]) for row in activity} == {
        ("active-super-admin", True),
        ("active-delegated-admin", True),
        ("active-dual-role-admin", True),
        ("suspended-dual-role-admin", False),
        ("archived-delegated-admin", False),
    }
    assert {row["user_id"] for row in admin_2sv_findings} == {
        "active-delegated-admin",
        "active-dual-role-admin",
    }
    assert {row["u"]["id"] for row in admin_2sv_visual_rows} == {
        "active-delegated-admin",
        "active-dual-role-admin",
    }
    assert admin_2sv_total == 3
    assert {row["user_id"] for row in dual_role_findings} == {
        "active-dual-role-admin",
    }
    assert {row["u"]["id"] for row in dual_role_visual_rows} == {
        "active-dual-role-admin",
    }
    assert dual_role_total == 2


def test_ai_admin_app_count_includes_non_ai_apps_in_eligible_population(
    neo4j_session,
) -> None:
    # Arrange
    _reset_graph(neo4j_session)
    _load_test_users(neo4j_session)
    neo4j_session.run(
        """
        MATCH (active_super:GoogleWorkspaceUser {id: 'active-super-admin'})
        MATCH (active_delegated:GoogleWorkspaceUser {id: 'active-delegated-admin'})
        MATCH (suspended:GoogleWorkspaceUser {id: 'suspended-dual-role-admin'})
        MATCH (archived:GoogleWorkspaceUser {id: 'archived-delegated-admin'})
        CREATE (ai_app:ThirdPartyApp {
            id: 'synthetic-ai-app',
            display_text: 'OpenAI Synthetic App'
        })
        CREATE (non_ai_app:ThirdPartyApp {
            id: 'synthetic-document-app',
            display_text: 'Synthetic Document Editor'
        })
        CREATE (inactive_only_app:ThirdPartyApp {
            id: 'synthetic-inactive-ai-app',
            display_text: 'Claude Synthetic Inactive App'
        })
        CREATE (active_super)-[:AUTHORIZED]->(ai_app)
        CREATE (active_delegated)-[:AUTHORIZED]->(non_ai_app)
        CREATE (suspended)-[:AUTHORIZED]->(inactive_only_app)
        CREATE (archived)-[:AUTHORIZED]->(inactive_only_app)
        """
    )
    fact = ai_admin_app_authorizations.facts[0]

    # Act
    findings = _run_query(neo4j_session, fact.cypher_query)
    visual_rows = list(neo4j_session.run(fact.cypher_visual_query))
    total = _count(neo4j_session, fact.cypher_count_query)

    # Assert
    assert len(findings) == 1
    assert {row["asset_node_id"] for row in findings} == {"synthetic-ai-app"}
    assert {row["app"]["id"] for row in visual_rows} == {"synthetic-ai-app"}
    assert total == 2
