from unittest.mock import patch

import cartography.intel.langsmith.deployments
import tests.data.langsmith.deployments
from tests.data.langsmith.deployments import SUPPORT_AGENT_ID
from tests.data.langsmith.deployments import TRIAGE_AGENT_ID
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID
from tests.integration.cartography.intel.langsmith.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


class _FakeClient:
    """Stands in for LangSmithClient on the per-deployment assistants data plane."""

    def search_assistants(self, deployment_url, tenant_id, page_size=100):
        return tests.data.langsmith.deployments.LANGSMITH_ASSISTANTS.get(
            deployment_url, []
        )


def _mock_get(client, org_id, workspace_id):
    return tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[workspace_id]


def _ensure_local_neo4j_has_test_deployments(neo4j_session):
    raw = (
        tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[WORKSPACE_PROD_ID]
        + tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[WORKSPACE_DEV_ID]
    )
    deployments = cartography.intel.langsmith.deployments.transform_deployments(raw)
    agents = cartography.intel.langsmith.deployments.merge_assistants(
        cartography.intel.langsmith.deployments.transform_agents(deployments),
        cartography.intel.langsmith.deployments.get_assistants(
            _FakeClient(), deployments
        ),
    )
    cartography.intel.langsmith.deployments.load_deployments(
        neo4j_session, agents, deployments, LANGSMITH_ORG_ID, TEST_UPDATE_TAG
    )
    by_workspace: dict[str, list[str]] = {}
    for deployment in deployments:
        by_workspace.setdefault(deployment["tenant_id"], []).append(deployment["id"])
    return agents, by_workspace


@patch.object(cartography.intel.langsmith.deployments, "get", side_effect=_mock_get)
def test_sync_langsmith_deployments(mock_get, neo4j_session):
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": LANGSMITH_ORG_ID,
    }

    agents, deployments_by_workspace = cartography.intel.langsmith.deployments.sync(
        neo4j_session,
        _FakeClient(),
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        common_job_parameters,
    )

    # The support deployment names its agent in an agent block; the triage deployment has
    # agent: null (the common case), so its agent is only found by listing assistants.
    assert {agent["id"] for agent in agents} == {SUPPORT_AGENT_ID, TRIAGE_AGENT_ID}
    assert sorted(deployments_by_workspace) == sorted(
        {WORKSPACE_PROD_ID, WORKSPACE_DEV_ID}
    )

    assert check_nodes(
        neo4j_session, "LangSmithDeployment", ["name", "shareable", "status"]
    ) == {
        ("support-bot", True, "READY"),
        ("triage-bot", False, "READY"),
    }

    # Assistant detail is merged onto the agent from the agent block; the environment
    # only the agent block knows is kept.
    assert check_nodes(
        neo4j_session, "LangSmithAgent", ["id", "graph_id", "environment"]
    ) == {
        (SUPPORT_AGENT_ID, "support_graph", "production"),
        (TRIAGE_AGENT_ID, "triage_graph", None),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithDeployment",
        "name",
        "LangSmithAgent",
        "id",
        "RUNS",
        rel_direction_right=True,
    ) == {
        ("support-bot", SUPPORT_AGENT_ID),
        ("triage-bot", TRIAGE_AGENT_ID),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithWorkspace",
        "id",
        "LangSmithDeployment",
        "name",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (WORKSPACE_PROD_ID, "support-bot"),
        (WORKSPACE_DEV_ID, "triage-bot"),
    }


@patch.object(cartography.intel.langsmith.deployments, "get", side_effect=_mock_get)
def test_deployment_secret_values_never_reach_the_graph(mock_get, neo4j_session):
    """
    The deployments API returns secrets as {name, value}. Only names may be ingested; the
    values must be dropped in transform, before load() is reached.
    """
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    cartography.intel.langsmith.deployments.sync(
        neo4j_session,
        _FakeClient(),
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    # secret_names is a list property, which check_nodes() cannot hash into a set.
    secret_names = neo4j_session.run(
        """
        MATCH (n:LangSmithDeployment)
        RETURN n.name AS name, n.secret_names AS secret_names
        ORDER BY name
        """
    ).data()
    assert [(r["name"], r["secret_names"]) for r in secret_names] == [
        ("support-bot", ["OPENAI_API_KEY", "SLACK_BOT_TOKEN"]),
        ("triage-bot", []),
    ]

    # No property on any node may contain a secret value from the fixture. List
    # properties are flattened so their elements are checked too.
    leaked = neo4j_session.run(
        """
        MATCH (n:LangSmithDeployment)
        UNWIND keys(n) AS k
        WITH n, k, n[k] AS v
        WITH n, k, CASE WHEN v IS :: LIST<ANY> THEN v ELSE [v] END AS values
        WHERE any(x IN values WHERE toString(x) CONTAINS 'SENTINEL-MUST-NOT-BE-INGESTED')
        RETURN n.name AS name, k AS property
        """
    ).data()
    assert leaked == []
