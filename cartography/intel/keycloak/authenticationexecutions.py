import logging
from collections import OrderedDict
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.keycloak.authenticationexecution import (
    ExecutionToExecutionMatchLink,
)
from cartography.models.keycloak.authenticationexecution import ExecutionToFlowMatchLink
from cartography.models.keycloak.authenticationexecution import (
    KeycloakAuthenticationExecutionSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
    flow_aliases: list[str],
) -> None:
    exec_by_flow = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
        flow_aliases,
    )
    transformed_exec, flow_steps, initial_flow_steps = transform(
        exec_by_flow, common_job_parameters["REALM"]
    )
    load_authenticationexecutions(
        neo4j_session,
        transformed_exec,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_execution_flow(
        neo4j_session,
        flow_steps,
        initial_flow_steps,
        common_job_parameters["REALM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session, base_url: str, realm: str, flow_aliases: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """Fetch authentication execution data for each flow from Keycloak API.

    Args:
        api_session: Authenticated requests session
        base_url: Keycloak base URL
        realm: Target realm name
        flow_aliases: List of authentication flow names to process

    Returns:
        Dictionary mapping flow names to their execution lists
    """
    results: dict[str, list[dict[str, Any]]] = {}
    for flow_name in flow_aliases:
        # URL-encode flow names to handle special characters safely
        encoded_flow_name = quote(flow_name, safe="")
        req = api_session.get(
            f"{base_url}/admin/realms/{realm}/authentication/flows/{encoded_flow_name}/executions",
            timeout=_TIMEOUT,
        )
        req.raise_for_status()
        results[flow_name] = req.json()
    return results


def _recursive_transform_flow(
    root_executions: list[dict[str, Any]],
) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """Recursively transforms Keycloak authentication executions into a flow graph structure.

    This function processes authentication executions and builds a directed graph representation
    suitable for Neo4j ingestion. It handles different execution requirements (REQUIRED,
    ALTERNATIVE, CONDITIONAL, DISABLED) and nested subflows.

    The function returns three components:
        - entries: Execution IDs that serve as entry points to the flow
        - links: Tuples representing directed edges between executions
        - outs: Execution IDs that serve as exit points from the flow

    Each execution dict must contain:
        - id: Unique execution identifier
        - requirement: Execution requirement type (REQUIRED/ALTERNATIVE/CONDITIONAL/DISABLED)
        - _children: List of nested child executions (for subflows)

    Args:
        root_executions: List of execution dictionaries to process

    Returns:
        A tuple containing (entry_points, execution_links, exit_points)
    """
    entries: list[str] = []
    links: list[tuple[str, str]] = []
    outs: list[str] = []

    for execution in root_executions:
        # Skip disabled executions as they don't participate in the flow
        if execution["requirement"] == "DISABLED":
            continue

        if execution["requirement"] == "REQUIRED":
            # If no entry point exists, this required execution becomes the flow's starting point
            if len(entries) == 0:
                entries.append(execution["id"])

            # Connect all current outputs to this required execution
            for i in outs:
                links.append((i, execution["id"]))

            # Handle subflow execution: recursively process children and wire them up
            if len(execution.get("_children", [])) > 0:
                c_ins, c_links, c_outs = _recursive_transform_flow(
                    execution["_children"]
                )
                for c_in in c_ins:
                    links.append((execution["id"], c_in))
                outs = c_outs
                links.extend(c_links)
            # For leaf executions, this becomes the sole output
            else:
                outs = [execution["id"]]  # Reset outs to the current execution

            continue

        if execution["requirement"] == "ALTERNATIVE":
            # Alternative executions create branching paths (OR logic)
            # This execution becomes an alternative entry point while preserving existing outputs
            entries.append(execution["id"])

            # Process subflow: wire up child inputs and aggregate child outputs
            if len(execution.get("_children", [])) > 0:
                c_ins, c_links, c_outs = _recursive_transform_flow(
                    execution["_children"]
                )
                for c_in in c_ins:
                    links.append((execution["id"], c_in))
                for c_out in c_outs:
                    outs.append(c_out)
                links.extend(c_links)
            else:
                outs.append(execution["id"])

            continue

        if execution["requirement"] == "CONDITIONAL":
            # Conditional executions only apply to subflows - skip if no children
            if len(execution.get("_children", [])) == 0:
                continue

            # Conditional logic creates two possible paths:
            # 1. Subflow evaluates to True: execution is treated as required
            # 2. Subflow evaluates to False: execution is skipped

            # Make this execution an entry point if none exist
            if len(entries) == 0:
                entries.append(execution["id"])

            # Connect all existing outputs to this conditional execution
            for i in outs:
                links.append((i, execution["id"]))

            # Process child executions recursively
            c_ins, c_links, c_outs = _recursive_transform_flow(execution["_children"])

            # Wire this execution to child entry points
            for c_in in c_ins:
                links.append((execution["id"], c_in))

            # Preserve both existing outputs and child outputs to model both conditional paths
            outs.extend(c_outs)

            # Add child links to the overall link collection
            links.extend(c_links)

    return entries, links, outs


def transform(
    exec_by_flow: dict[str, list[dict[str, Any]]], realm: str
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    transformed_by_id: OrderedDict[str, dict[str, Any]] = OrderedDict()
    initial_flow_steps: list[dict[str, str]] = []
    flow_steps: list[dict[str, str]] = []

    for flow_name, executions in exec_by_flow.items():
        _parent_by_level: dict[int, str] = {}
        _root_executions: list[dict[str, Any]] = []

        # Transform executions to include parent flow/subflow relationships
        # and create a hierarchical structure for graph processing
        for execution in executions:
            # Level 0 executions belong directly to the named flow
            if execution["level"] == 0:
                execution["_parent_flow"] = flow_name
                _root_executions.append(execution)
            else:
                # Nested executions belong to their parent subflow
                execution["_parent_subflow"] = _parent_by_level[execution["level"] - 1]
                transformed_by_id[execution["_parent_subflow"]]["_children"].append(
                    execution
                )

            # Track subflow parents for the next nesting level
            if execution.get("authenticationFlow", True):
                _parent_by_level[execution["level"]] = execution["id"]

            execution["_children"] = []
            execution["is_terminal_step"] = False  # Placeholder for terminal step flag
            transformed_by_id[execution["id"]] = execution

        # Process authentication flow structure and build execution graph
        # Reference: https://www.keycloak.org/docs/latest/server_admin/index.html#_execution-requirements
        entries, links, terminals = _recursive_transform_flow(_root_executions)

        for entry in entries:
            initial_flow_steps.append(
                {
                    "flow_name": flow_name,
                    "execution_id": entry,
                    "realm": realm,
                }
            )

        for link in links:
            flow_steps.append(
                {
                    "source": link[0],
                    "target": link[1],
                }
            )

        for node_id in terminals:
            transformed_by_id[node_id]["is_terminal_step"] = True

    return list(transformed_by_id.values()), flow_steps, initial_flow_steps


@timeit
def load_authenticationexecutions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Keycloak AuthenticationExecutions (%s) into Neo4j.",
        len(data),
        realm,
    )
    load(
        neo4j_session,
        KeycloakAuthenticationExecutionSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


def load_execution_flow(
    neo4j_session: neo4j.Session,
    flow_steps: list[dict[str, Any]],
    initial_flow_steps: list[dict[str, str]],
    realm_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        ExecutionToExecutionMatchLink(),
        flow_steps,
        LASTUPDATED=update_tag,
        _sub_resource_label="KeycloakRealm",
        _sub_resource_id=realm_id,
    )
    load_matchlinks(
        neo4j_session,
        ExecutionToFlowMatchLink(),
        initial_flow_steps,
        LASTUPDATED=update_tag,
        _sub_resource_label="KeycloakRealm",
        _sub_resource_id=realm_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        KeycloakAuthenticationExecutionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        ExecutionToExecutionMatchLink(),
        "KeycloakRealm",
        common_job_parameters["REALM_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        ExecutionToFlowMatchLink(),
        "KeycloakRealm",
        common_job_parameters["REALM_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
