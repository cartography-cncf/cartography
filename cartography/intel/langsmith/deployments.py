import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithPermissionError
from cartography.models.langsmith.agent import LangSmithAgentSchema
from cartography.models.langsmith.deployment import LangSmithDeploymentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Only a READY deployment is actually serving; the other states are provisioning,
# unused, or being torn down, so probing them costs a timeout and returns nothing.
# Note DEPLOYED is a *revision* status, not a deployment status.
_SERVING_STATUS = "READY"
# Assistant searches hit each deployment's own data plane, so they parallelise well.
_MAX_ASSISTANT_WORKERS = 10


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]], bool]:
    """
    Load deployments and any agents they serve.

    Returns the agent inventory, a workspace -> deployment ids mapping, and whether the
    collection completed. Callers must not clean up on an incomplete collection.
    """
    raw: list[dict[str, Any]] = []
    complete = True
    for workspace in workspaces:
        try:
            raw.extend(get(client, org_id, workspace["id"]))
        except LangSmithPermissionError as err:
            # deployments:read is commonly absent in some workspaces.
            logger.warning(
                "Skipping LangSmith deployments for workspace %s: %s",
                workspace["id"],
                err,
            )
            complete = False
            continue

    deployments = transform_deployments(raw)
    agents = transform_agents(deployments, org_id)
    assistants, assistants_complete = get_assistants(client, deployments, org_id)
    complete = complete and assistants_complete
    agents = merge_assistants(agents, assistants)
    load_deployments(
        neo4j_session, agents, deployments, org_id, common_job_parameters["UPDATE_TAG"]
    )
    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        # Deleting on a partial collection would erase deployments and agents that still
        # exist, and their credentials with them. Stale nodes are the lesser harm.
        logger.warning(
            "Skipping LangSmith deployment cleanup for organization %s: collection was "
            "incomplete, so existing nodes are preserved rather than deleted.",
            org_id,
        )

    deployments_by_workspace: dict[str, list[str]] = {}
    for deployment in deployments:
        deployments_by_workspace.setdefault(deployment["tenant_id"], []).append(
            deployment["id"]
        )
    return agents, deployments_by_workspace, complete


@timeit
def get_assistants(
    client: LangSmithClient, deployments: list[dict[str, Any]], org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Enumerate the assistants served by each deployment.

    A LangSmith agent id is an assistant id, and assistants are only listable on each
    deployment's own data plane, one request per deployment. Deployments without a serving
    URL, or not in a serving state, are skipped: they cannot answer, and a scaled-to-zero
    or half-provisioned deployment costs a full timeout to discover that.

    The remaining requests run concurrently, because they target independent hosts.
    """
    candidates = [
        deployment
        for deployment in deployments
        if deployment.get("url") and deployment.get("status") == _SERVING_STATUS
    ]
    skipped = len(deployments) - len(candidates)
    if skipped:
        logger.debug(
            "Skipping assistant search for %d deployment(s) that are not %s or have no URL",
            skipped,
            _SERVING_STATUS,
        )
    if not candidates:
        return [], True

    worker_count = min(_MAX_ASSISTANT_WORKERS, len(candidates))
    logger.info(
        "Searching assistants across %d LangSmith deployment(s) with %d workers",
        len(candidates),
        worker_count,
    )
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(
            executor.map(
                lambda deployment: _assistants_for(client, deployment, org_id),
                candidates,
            )
        )
    complete = all(ok for _, ok in results)
    if not complete:
        logger.warning(
            "Assistant discovery was incomplete for at least one deployment; agent "
            "cleanup will be skipped so existing agents are not deleted.",
        )
    return [assistant for batch, _ in results for assistant in batch], complete


def _assistants_for(
    client: LangSmithClient, deployment: dict[str, Any], org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """Shape one deployment's assistants, and report whether the listing completed."""
    assistants, complete = client.search_assistants(
        deployment["url"], deployment["tenant_id"]
    )
    return [
        {
            "id": f"{org_id}|{assistant['assistant_id']}",
            "assistant_id": assistant["assistant_id"],
            "name": assistant.get("name"),
            "graph_id": assistant.get("graph_id"),
            "description": assistant.get("description"),
            "version": assistant.get("version"),
            "environment": None,
            "deployment_ids": [deployment["id"]],
            "created_at": assistant.get("created_at"),
            "updated_at": assistant.get("updated_at"),
        }
        for assistant in assistants
    ], complete


def merge_assistants(
    agents: list[dict[str, Any]], assistants: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Combine agents named by a deployment's agent block with those found via assistants.

    LangGraph derives an assistant id from its graph, so two deployments running the same
    graph expose the same assistant id. Serving deployments therefore accumulate into a
    list rather than overwriting one another.
    """
    merged: dict[str, dict[str, Any]] = {}
    for agent in agents:
        record = dict(agent)
        record.setdefault("deployment_ids", [])
        merged[record["id"]] = record
    for assistant in assistants:
        existing = merged.get(assistant["id"])
        if existing is None:
            merged[assistant["id"]] = dict(assistant)
            continue
        deployment_ids = existing.get("deployment_ids") or []
        for deployment_id in assistant.get("deployment_ids") or []:
            if deployment_id not in deployment_ids:
                deployment_ids.append(deployment_id)
        existing.update(
            {
                k: v
                for k, v in assistant.items()
                if v is not None and k != "deployment_ids"
            }
        )
        existing["deployment_ids"] = deployment_ids
    return list(merged.values())


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
        transformed.append(
            {
                "id": deployment["id"],
                "tenant_id": deployment["tenant_id"],
                "name": deployment.get("name"),
                "display_name": deployment.get("display_name"),
                "status": deployment.get("status"),
                "url": deployment.get("url"),
                "source": deployment.get("source"),
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
    deployments: list[dict[str, Any]], org_id: str
) -> list[dict[str, Any]]:
    """
    Derive the agent inventory from the deployments that serve them.

    Only deployments created with an explicit agent/environment binding carry an agent
    block; for most deployments it is null, and their agents are found by listing the
    deployment's assistants instead.
    """
    agents: dict[str, dict[str, Any]] = {}
    for deployment in deployments:
        agent_id = deployment.get("agent_id")
        if not agent_id:
            continue
        record = agents.setdefault(
            agent_id,
            {
                "id": f"{org_id}|{agent_id}",
                "assistant_id": agent_id,
                "name": deployment.get("display_name") or deployment.get("name"),
                "environment": deployment.get("agent_environment"),
                "deployment_ids": [],
            },
        )
        record["deployment_ids"].append(deployment["id"])
    return list(agents.values())


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
    load(
        neo4j_session,
        LangSmithDeploymentSchema(),
        deployments,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithAgentSchema(),
        agents,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(LangSmithDeploymentSchema(), common_job_parameters).run(
        neo4j_session
    )
