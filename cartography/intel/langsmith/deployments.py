import logging
from typing import Any

import neo4j

from cartography.intel.langsmith.util import cleanup_workspaces
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import load_by_workspace
from cartography.intel.langsmith.util import resolve_ls_user_id
from cartography.models.langsmith.agent import LangSmithAgentSchema
from cartography.models.langsmith.deployment import LangSmithDeploymentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    user_lookup: dict[str, str],
    common_job_parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Load deployments and the agents in the control plane's agent registry.

    Returns one agent row per workspace the agent was seen in, and the workspaces whose
    agent inventory is complete. Agents are cleaned up by the agent_auth sync, which also
    loads them, so it must clean up only those workspaces.

    Agents come from the control plane only. A deployment's own data plane can also list
    its assistants, but this module never calls it: the deployment runs code its authors
    control, including custom auth and middleware that see every request header, so any
    request there would hand them the organization token.
    """
    raw: list[dict[str, Any]] = []
    readable_workspace_ids: set[str] = set()
    for workspace in workspaces:
        try:
            raw.extend(get(client, org_id, workspace["id"]))
        except LangSmithFetchError as err:
            # deployments:read is commonly absent in some workspaces.
            logger.warning(
                "Skipping LangSmith deployments for workspace %s: %s",
                workspace["id"],
                err,
            )
            if err.not_found:
                readable_workspace_ids.add(workspace["id"])
            continue
        readable_workspace_ids.add(workspace["id"])

    deployments = transform_deployments(raw)
    registry_agents, registry_readable = get_agents(client, org_id, workspaces)
    agents = transform_agents(deployments, registry_agents, org_id, user_lookup)
    load_deployments(
        neo4j_session, agents, deployments, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup_workspaces(
        neo4j_session,
        LangSmithDeploymentSchema(),
        readable_workspace_ids,
        common_job_parameters,
    )
    return agents, readable_workspace_ids & registry_readable


@timeit
def get(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> list[dict[str, Any]]:
    return client.get_paginated_envelope(
        "/v2/deployments",
        key="resources",
        org_id=org_id,
        tenant_id=workspace_id,
        host=True,
    )


@timeit
def get_agents(
    client: LangSmithClient, org_id: str, workspaces: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Read the agent registry in every workspace.

    Returns one record per agent per workspace it is visible from, and the workspaces whose
    registry listing completed.
    """
    records: list[dict[str, Any]] = []
    readable_workspace_ids: set[str] = set()
    for workspace in workspaces:
        workspace_id = workspace["id"]
        try:
            rows = client.get_cursor_paginated(
                "/api/v1/agents",
                key="items",
                org_id=org_id,
                tenant_id=workspace_id,
            )
        except LangSmithFetchError as err:
            logger.warning(
                "Skipping LangSmith agents for workspace %s: %s", workspace_id, err
            )
            if err.not_found:
                readable_workspace_ids.add(workspace_id)
            continue
        readable_workspace_ids.add(workspace_id)
        for row in rows:
            records.append({**row, "workspace_id": workspace_id})
    return records, readable_workspace_ids


def transform_deployments(deployments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Shape deployments for ingest.

    The deployments API returns environment secrets as {name, value} pairs. Only the names
    are kept: the values are dropped here, before the records reach load(), so secret
    material is never written to the graph.
    """
    transformed = []
    for deployment in deployments:
        agent = deployment.get("agent") or {}
        source_config = deployment.get("source_config") or {}
        transformed.append(
            {
                "id": deployment["id"],
                "tenant_id": deployment["tenant_id"],
                "name": deployment.get("name"),
                "display_name": deployment.get("display_name"),
                "status": deployment.get("status"),
                "url": deployment.get("url"),
                "source": deployment.get("source"),
                "repo_url": source_config.get("repo_url"),
                "build_on_push": source_config.get("build_on_push"),
                "custom_url": source_config.get("custom_url"),
                "listener_id": source_config.get("listener_id"),
                "image_version": deployment.get("image_version"),
                "shareable": deployment.get("shareable"),
                "route_through_gateway": deployment.get("route_through_gateway"),
                "is_managed_deep_agent": deployment.get("is_managed_deep_agent"),
                "is_preview": deployment.get("is_preview"),
                "tracer_session_id": deployment.get("tracer_session_id"),
                "created_at": deployment.get("created_at"),
                "updated_at": deployment.get("updated_at"),
                "agent_id": agent.get("agent_id"),
                "agent_environment": agent.get("environment"),
                "secret_names": sorted(
                    secret["name"]
                    for secret in (deployment.get("secrets") or [])
                    if secret.get("name")
                ),
                "secret_reference_names": sorted(
                    reference["name"]
                    for reference in (deployment.get("secret_references") or [])
                    if reference.get("name")
                ),
            }
        )
    return transformed


def transform_agents(
    deployments: list[dict[str, Any]],
    registry_agents: list[dict[str, Any]],
    org_id: str,
    user_lookup: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Merge the agent registry with the agents that deployments name, one row per agent per
    workspace.

    The registry carries each agent's owner and environments. An environment traces into a
    tracing project, and so does the deployment serving it, so a shared project links the
    two without reading every agent's runtime bindings, which costs one request per agent.
    A deployment also names its agent in an agent block when it was created with an
    explicit agent/environment binding.
    """
    deployments_by_project: dict[str, list[str]] = {}
    for deployment in deployments:
        if deployment.get("tracer_session_id"):
            deployments_by_project.setdefault(
                deployment["tracer_session_id"], []
            ).append(deployment["id"])
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for agent in registry_agents:
        environments = agent.get("environments") or []
        rows[(agent["id"], agent["workspace_id"])] = {
            "id": f"{org_id}|{agent['id']}",
            "agent_id": agent["id"],
            "workspace_id": agent["workspace_id"],
            "name": agent.get("name"),
            "agent_type": agent.get("agent_type"),
            "source_type": agent.get("source_type"),
            "environments": sorted(
                {
                    environment["environment"].lower()
                    for environment in environments
                    if environment.get("environment")
                }
            ),
            "owner_ls_user_id": resolve_ls_user_id(
                agent.get("owner_id") or agent.get("owner"), user_lookup
            ),
            "created_at": agent.get("created_at"),
            "deployment_ids": sorted(
                {
                    deployment_id
                    for environment in environments
                    for deployment_id in deployments_by_project.get(
                        environment.get("tracer_session_id") or "", []
                    )
                }
            ),
        }
    for deployment in deployments:
        agent_id = deployment.get("agent_id")
        if not agent_id:
            continue
        record = rows.setdefault(
            (agent_id, deployment["tenant_id"]),
            {
                "id": f"{org_id}|{agent_id}",
                "agent_id": agent_id,
                "workspace_id": deployment["tenant_id"],
                "name": deployment.get("display_name") or deployment.get("name"),
                "environments": [],
                "deployment_ids": [],
            },
        )
        if deployment["id"] not in record["deployment_ids"]:
            record["deployment_ids"].append(deployment["id"])
        environment = (deployment.get("agent_environment") or "").lower()
        if environment and environment not in record["environments"]:
            record["environments"] = sorted([*record["environments"], environment])
    return list(rows.values())


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    agents: list[dict[str, Any]],
    deployments: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    # Deployments must land before agents: every agent carries the ids of the deployments
    # serving it, and that one-to-many RUNS edge can only match deployments that exist.
    load_by_workspace(
        neo4j_session,
        LangSmithDeploymentSchema(),
        [
            {**deployment, "workspace_id": deployment["tenant_id"]}
            for deployment in deployments
        ],
        org_id,
        update_tag,
    )
    load_by_workspace(neo4j_session, LangSmithAgentSchema(), agents, org_id, update_tag)
