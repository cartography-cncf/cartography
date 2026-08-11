from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.agent import AnthropicAgentSchema
from cartography.models.anthropic.deployment import AnthropicDeploymentSchema
from cartography.models.anthropic.environment import AnthropicEnvironmentSchema
from cartography.models.anthropic.memorystore import AnthropicMemoryStoreSchema
from cartography.models.anthropic.vault import AnthropicVaultSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Beta headers are sent per request, not on the session: managed-agents and
# agent-memory are mutually exclusive and sending both returns a 400.
_MANAGED_AGENTS_HEADERS = {"anthropic-beta": "managed-agents-2026-04-01"}
_AGENT_MEMORY_HEADERS = {"anthropic-beta": "agent-memory-2026-07-22"}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    base_url = common_job_parameters["BASE_URL"]
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    # Load in dependency order: deployments reference agents, environments and
    # vaults, and agents reference skills loaded by the skills sync.
    environments = get_environments(api_session, base_url)
    for environment in environments:
        transform_environment(environment)
    load_environments(neo4j_session, environments, workspace_id, update_tag)

    vaults = get_vaults(api_session, base_url)
    load_vaults(neo4j_session, vaults, workspace_id, update_tag)

    memory_stores = get_memory_stores(api_session, base_url)
    load_memory_stores(neo4j_session, memory_stores, workspace_id, update_tag)

    agents = get_agents(api_session, base_url)
    for agent in agents:
        transform_agent(agent)
    load_agents(neo4j_session, agents, workspace_id, update_tag)

    deployments = get_deployments(api_session, base_url)
    load_deployments(neo4j_session, deployments, workspace_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_agents(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/agents",
        timeout=_TIMEOUT,
        headers=_MANAGED_AGENTS_HEADERS,
    )


@timeit
def get_environments(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/environments",
        timeout=_TIMEOUT,
        headers=_MANAGED_AGENTS_HEADERS,
    )


@timeit
def get_deployments(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/deployments",
        timeout=_TIMEOUT,
        headers=_MANAGED_AGENTS_HEADERS,
    )


@timeit
def get_vaults(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/vaults",
        timeout=_TIMEOUT,
        headers=_MANAGED_AGENTS_HEADERS,
    )


@timeit
def get_memory_stores(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/memory_stores",
        timeout=_TIMEOUT,
        headers=_AGENT_MEMORY_HEADERS,
    )


def transform_agent(agent: dict[str, Any]) -> None:
    """Flatten the agent's nested MCP server, tool and skill lists.

    Tools are split by permission policy rather than kept as one list: the ones an
    agent may invoke without asking run unsupervised, which is the part worth
    querying on.
    """
    agent["mcp_server_urls"] = [
        server["url"] for server in agent.get("mcp_servers") or [] if server.get("url")
    ]
    agent["skill_ids"] = [
        skill["skill_id"]
        for skill in agent.get("skills") or []
        if skill.get("skill_id")
    ]
    always_allow: list[str] = []
    always_ask: list[str] = []
    for tool in agent.get("tools") or []:
        name = tool.get("name") or tool.get("type")
        if not name:
            continue
        if tool.get("permission_policy") == "always_allow":
            always_allow.append(name)
        else:
            always_ask.append(name)
    agent["always_allow_tools"] = sorted(always_allow)
    agent["always_ask_tools"] = sorted(always_ask)


def transform_environment(environment: dict[str, Any]) -> None:
    """Flatten the environment's config union into the egress policy it encodes."""
    config = environment.pop("config", None) or {}
    environment["config_type"] = config.get("type", "cloud")
    networking = config.get("networking")
    if isinstance(networking, str):
        # The unrestricted case is the bare string rather than an object.
        environment["networking_type"] = networking
        networking = {}
    else:
        networking = networking or {}
        environment["networking_type"] = networking.get("type")
    environment["allowed_hosts"] = networking.get("allowed_hosts")
    environment["allow_mcp_servers"] = networking.get("allow_mcp_servers")
    environment["allow_package_managers"] = networking.get("allow_package_managers")


@timeit
def load_agents(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicAgentSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicDeploymentSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def load_vaults(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicVaultSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def load_memory_stores(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicMemoryStoreSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Reverse of the load order: dependants first.
    for schema in (
        AnthropicDeploymentSchema(),
        AnthropicAgentSchema(),
        AnthropicMemoryStoreSchema(),
        AnthropicVaultSchema(),
        AnthropicEnvironmentSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
