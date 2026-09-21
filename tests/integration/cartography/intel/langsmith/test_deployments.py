from unittest.mock import patch

import cartography.intel.langsmith.deployments
import tests.data.langsmith.deployments
from tests.data.langsmith.deployments import SUPPORT_AGENT_ID
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


def _mock_get(client, org_id, workspace_id):
    return tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[workspace_id]


def _ensure_local_neo4j_has_test_deployments(neo4j_session):
    raw = (
        tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[WORKSPACE_PROD_ID]
        + tests.data.langsmith.deployments.LANGSMITH_DEPLOYMENTS[WORKSPACE_DEV_ID]
    )
    deployments = cartography.intel.langsmith.deployments.transform_deployments(raw)
    agents = cartography.intel.langsmith.deployments.transform_agents(deployments)
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
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        common_job_parameters,
    )

    # Only the deployment with an explicit agent block yields an agent node; the other
    # has agent: null, which is the common case in practice.
    assert {agent["id"] for agent in agents} == {SUPPORT_AGENT_ID}
    assert sorted(deployments_by_workspace) == sorted(
        {WORKSPACE_PROD_ID, WORKSPACE_DEV_ID}
    )

    assert check_nodes(
        neo4j_session, "LangSmithDeployment", ["name", "shareable", "status"]
    ) == {
        ("support-bot", True, "DEPLOYED"),
        ("triage-bot", False, "DEPLOYED"),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithDeployment",
        "name",
        "LangSmithAgent",
        "id",
        "RUNS",
        rel_direction_right=True,
    ) == {("support-bot", SUPPORT_AGENT_ID)}

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
        None,
        LANGSMITH_ORG_ID,
        LANGSMITH_WORKSPACES,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": LANGSMITH_ORG_ID},
    )

    assert check_nodes(
        neo4j_session, "LangSmithDeployment", ["name", "secret_names"]
    ) == {
        ("support-bot", ["OPENAI_API_KEY", "SLACK_BOT_TOKEN"]),
        ("triage-bot", []),
    }

    # No property on any node may contain a secret value from the fixture.
    leaked = neo4j_session.run(
        """
        MATCH (n:LangSmithDeployment)
        UNWIND keys(n) AS k
        WITH n, k, toString(n[k]) AS v
        WHERE v CONTAINS 'SENTINEL-MUST-NOT-BE-INGESTED'
        RETURN n.name AS name, k AS property
        """
    ).data()
    assert leaked == []
