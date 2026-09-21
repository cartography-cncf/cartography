from unittest.mock import patch

import cartography.intel.langsmith.agent_auth
import tests.data.langsmith.agent_auth
from tests.data.langsmith.deployments import SUPPORT_AGENT_ID
from tests.data.langsmith.deployments import TRIAGE_AGENT_ID
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.integration.cartography.intel.langsmith.test_deployments import (
    _ensure_local_neo4j_has_test_deployments,
)
from tests.integration.cartography.intel.langsmith.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _providers(client, org_id, workspaces):
    return [
        cartography.intel.langsmith.agent_auth.transform_provider(
            provider, is_platform=False
        )
        for provider in tests.data.langsmith.agent_auth.LANGSMITH_OAUTH_PROVIDERS
    ]


def _connections(client, org_id, workspaces, agents):
    connections = []
    for agent in agents:
        payload = tests.data.langsmith.agent_auth.LANGSMITH_AGENT_CONNECTIONS.get(
            agent["id"], {"data": []}
        )
        for row in payload["data"]:
            connections.append(dict(row))
    return connections


@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_connections",
    side_effect=_connections,
)
@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_providers",
    side_effect=_providers,
)
def test_sync_langsmith_agent_auth(mock_providers, mock_connections, neo4j_session):
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    users = _ensure_local_neo4j_has_test_users(neo4j_session)
    agents, _ = _ensure_local_neo4j_has_test_deployments(neo4j_session)

    cartography.intel.langsmith.agent_auth.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        agents,
        users,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    # Providers from both agent-auth subsystems land in one node type.
    assert check_nodes(
        neo4j_session, "LangSmithOAuthProvider", ["provider_id", "is_platform_provider"]
    ) == {
        ("github-prod", False),
        ("google-workspace", False),
    }


@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_connections",
    side_effect=_connections,
)
@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_providers",
    side_effect=_providers,
)
def test_agent_to_user_oauth_token_edges(
    mock_providers, mock_connections, neo4j_session
):
    """
    The central question this module exists to answer: which agent can act as which human,
    against which third-party provider.
    """
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    users = _ensure_local_neo4j_has_test_users(neo4j_session)
    agents, _ = _ensure_local_neo4j_has_test_deployments(neo4j_session)

    cartography.intel.langsmith.agent_auth.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        agents,
        users,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    result = neo4j_session.run(
        """
        MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
              -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
        MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
        RETURN a.id AS agent, u.email AS email, p.provider_id AS provider,
               c.scopes AS scopes
        """
    ).data()
    actual = {
        (r["agent"], r["email"], r["provider"], tuple(r["scopes"])) for r in result
    }
    assert actual == {
        (
            SUPPORT_AGENT_ID,
            "mbsimpson@simpson.corp",
            "github-prod",
            ("repo", "read:org"),
        ),
        (
            SUPPORT_AGENT_ID,
            "hjsimpson@simpson.corp",
            "google-workspace",
            ("https://www.googleapis.com/auth/gmail.readonly",),
        ),
        (TRIAGE_AGENT_ID, "bjsimpson@simpson.corp", "github-prod", ("repo",)),
    }


@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_connections",
    side_effect=_connections,
)
@patch.object(
    cartography.intel.langsmith.agent_auth,
    "get_providers",
    side_effect=_providers,
)
def test_deactivated_user_still_has_agent_acting_for_them(
    mock_providers, mock_connections, neo4j_session
):
    """Deactivating a LangSmith identity does not revoke agent credentials held for them."""
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    users = _ensure_local_neo4j_has_test_users(neo4j_session)
    agents, _ = _ensure_local_neo4j_has_test_deployments(neo4j_session)

    cartography.intel.langsmith.agent_auth.sync(
        neo4j_session,
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        agents,
        users,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    result = neo4j_session.run(
        """
        MATCH (u:LangSmithUser {is_disabled: true})<-[:ON_BEHALF_OF]-(c:LangSmithAgentCredential)
        MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c)
        RETURN u.email AS email, a.id AS agent
        """
    ).data()
    assert [(r["email"], r["agent"]) for r in result] == [
        ("bjsimpson@simpson.corp", TRIAGE_AGENT_ID)
    ]
