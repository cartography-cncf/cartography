import copy
from unittest.mock import patch

import requests

import cartography.intel.anthropic.agents
import tests.data.anthropic.agents
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_skills import (
    _ensure_local_neo4j_has_test_skills,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"


@patch.object(
    cartography.intel.anthropic.agents,
    "get_deployments",
    return_value=copy.deepcopy(tests.data.anthropic.agents.ANTHROPIC_DEPLOYMENTS),
)
@patch.object(
    cartography.intel.anthropic.agents,
    "get_agents",
    return_value=copy.deepcopy(tests.data.anthropic.agents.ANTHROPIC_AGENTS),
)
@patch.object(
    cartography.intel.anthropic.agents,
    "get_memory_stores",
    return_value=copy.deepcopy(tests.data.anthropic.agents.ANTHROPIC_MEMORY_STORES),
)
@patch.object(
    cartography.intel.anthropic.agents,
    "get_vaults",
    return_value=copy.deepcopy(tests.data.anthropic.agents.ANTHROPIC_VAULTS),
)
@patch.object(
    cartography.intel.anthropic.agents,
    "get_environments",
    return_value=copy.deepcopy(tests.data.anthropic.agents.ANTHROPIC_ENVIRONMENTS),
)
def test_load_anthropic_agents(
    mock_envs, mock_vaults, mock_memory, mock_agents, mock_deployments, neo4j_session
):
    """
    Ensure agents, environments, vaults, memory stores and deployments get loaded
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_skills(neo4j_session)

    # Act
    cartography.intel.anthropic.agents.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert environments exist with the egress policy flattened out of the config
    # union. The unrestricted case arrives as a bare string rather than an object.
    assert check_nodes(
        neo4j_session,
        "AnthropicEnvironment",
        ["id", "networking_type", "allow_package_managers"],
    ) == {
        ("env_01Kd7Rt2Nm5Bq8Vx3Wy6Pz9L", "limited", False),
        ("env_02Wq4Jm9Zn6Rt1Cx8Bv5Hd3K", "unrestricted", None),
    }

    # Assert vaults and memory stores exist
    assert check_nodes(neo4j_session, "AnthropicVault", ["id", "display_name"]) == {
        ("vlt_01Tz6Nb3Kw8Qm2Xr5Jd9Pc4V", "plant-credentials"),
    }
    assert check_nodes(neo4j_session, "AnthropicMemoryStore", ["id", "name"]) == {
        ("memstore_01Bd8Vq5Rk2Wn7Tj4Lm6Zx3C", "shift-handover"),
    }

    # Assert the agent exists with its tools split by permission policy: the
    # always_allow ones run unsupervised
    assert check_nodes(
        neo4j_session, "AnthropicAgent", ["id", "name", "model_id"]
    ) == {
        ("agent_01Rn5Wx9Kt3Bm7Qd2Vz8Lp6J", "reactor-monitor", "claude-opus-5"),
    }
    agent = neo4j_session.run(
        "MATCH (a:AnthropicAgent) RETURN a.always_allow_tools AS allow, "
        "a.always_ask_tools AS ask, a.mcp_server_urls AS mcp"
    ).single()
    assert agent["allow"] == ["read_sensor"]
    assert agent["ask"] == ["scram_reactor"]
    assert agent["mcp"] == ["https://mcp.springfield.corp"]

    # Assert the agent is linked to the skill it loads
    assert check_rels(
        neo4j_session,
        "AnthropicAgent",
        "id",
        "AnthropicSkill",
        "id",
        "USES_SKILL",
        rel_direction_right=True,
    ) == {
        (
            "agent_01Rn5Wx9Kt3Bm7Qd2Vz8Lp6J",
            "skill_01Mv4Zq7Nr2Ks8Ld3Tp6Wx9B",
        ),
    }

    # Assert the deployment exists and carries its schedule
    assert check_nodes(
        neo4j_session,
        "AnthropicDeployment",
        ["id", "status", "schedule_expression"],
    ) == {
        ("depl_01Ym2Qc7Jx4Nv9Rb5Kd8Tw3P", "active", "0 * * * *"),
    }

    # Assert the deployment wires the agent to the sandbox and credentials it runs
    # with: this is the standing-execution blast radius
    assert check_rels(
        neo4j_session,
        "AnthropicDeployment",
        "id",
        "AnthropicAgent",
        "id",
        "RUNS",
        rel_direction_right=True,
    ) == {("depl_01Ym2Qc7Jx4Nv9Rb5Kd8Tw3P", "agent_01Rn5Wx9Kt3Bm7Qd2Vz8Lp6J")}
    assert check_rels(
        neo4j_session,
        "AnthropicDeployment",
        "id",
        "AnthropicEnvironment",
        "id",
        "RUNS_IN",
        rel_direction_right=True,
    ) == {("depl_01Ym2Qc7Jx4Nv9Rb5Kd8Tw3P", "env_01Kd7Rt2Nm5Bq8Vx3Wy6Pz9L")}
    assert check_rels(
        neo4j_session,
        "AnthropicDeployment",
        "id",
        "AnthropicVault",
        "id",
        "USES_VAULT",
        rel_direction_right=True,
    ) == {("depl_01Ym2Qc7Jx4Nv9Rb5Kd8Tw3P", "vlt_01Tz6Nb3Kw8Qm2Xr5Jd9Pc4V")}

    # Assert every workspace-plane node is scoped to its workspace
    for label in (
        "AnthropicAgent",
        "AnthropicEnvironment",
        "AnthropicDeployment",
        "AnthropicVault",
        "AnthropicMemoryStore",
    ):
        assert {
            workspace_id
            for _, workspace_id in check_rels(
                neo4j_session,
                label,
                "id",
                "AnthropicWorkspace",
                "id",
                "RESOURCE",
                rel_direction_right=False,
            )
        } == {TEST_WORKSPACE_ID}
