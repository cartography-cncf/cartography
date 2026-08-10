import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.workspace_assignment import (
    DatabricksAccountGroupWorkspaceAssignmentRel,
)
from cartography.models.databricks.workspace_assignment import (
    DatabricksAccountServicePrincipalWorkspaceAssignmentRel,
)
from cartography.models.databricks.workspace_assignment import (
    DatabricksAccountUserWorkspaceAssignmentRel,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ASSIGNMENT_RELS = (
    DatabricksAccountUserWorkspaceAssignmentRel(),
    DatabricksAccountGroupWorkspaceAssignmentRel(),
    DatabricksAccountServicePrincipalWorkspaceAssignmentRel(),
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    workspace_node_ids: dict[str, str],
    common_job_parameters: dict[str, Any],
) -> None:
    assignments, complete = get(api_session, workspace_node_ids)
    transformed = transform(assignments, account_id)
    load_assignments(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    # Only clean up when every workspace's assignments were read this run. A
    # 403/404 on one workspace means its assignments were not refreshed, so a
    # whole-account MatchLink cleanup would delete still-valid ASSIGNED_TO edges
    # for it; skip cleanup and let a fully successful run reconcile stale edges.
    if complete:
        cleanup(neo4j_session, account_id, common_job_parameters["UPDATE_TAG"])
    else:
        logger.warning(
            "Databricks workspace assignments were partially read for account "
            "%s; skipping ASSIGNED_TO cleanup to avoid deleting valid edges.",
            account_id,
        )


@timeit
def get(
    api_session: DatabricksAccountClient, workspace_node_ids: dict[str, str]
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch permission assignments for each account workspace.

    Returns ``(assignments, complete)`` where each assignment is one row per
    (principal, workspace) carrying the SCIM ``principal_id`` (resolved to a node
    in transform), the target workspace node id, and the granted ``permissions``
    list, so a downstream MatchLink attaches it to the right principal.
    ``complete`` is False when any workspace's assignments were skipped (403/404)
    so the caller can skip cleanup.
    """
    assignments: list[dict[str, Any]] = []
    complete = True
    for numeric_id, workspace_node_id in workspace_node_ids.items():
        uri = api_session.account_uri(f"/workspaces/{numeric_id}/permissionassignments")
        try:
            data = api_session.get(uri)
        except requests.HTTPError as e:
            # A workspace the caller can't read assignments on (403) or that
            # vanished mid-sync (404) is skippable; any other error must abort so
            # the assignment cleanup does not drop still-valid ASSIGNED_TO edges.
            skip_or_raise_http(e, 403, 404)
            complete = False
            logger.warning(
                "Skipping permission assignments for workspace %s: %s", numeric_id, e
            )
            continue
        for entry in data.get("permission_assignments", []) or []:
            principal = entry.get("principal") or {}
            principal_id = principal.get("principal_id")
            permissions = entry.get("permissions") or []
            if principal_id is None or not permissions:
                continue
            assignments.append(
                {
                    "principal_id": principal_id,
                    "workspace_node_id": workspace_node_id,
                    "permissions": permissions,
                }
            )
    return assignments, complete


@timeit
def transform(
    assignments: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    """Resolve each assignment's SCIM principal id to its account-scoped node id.

    Feeding every row to all three principal MatchLinks lets the matchers decide
    which node label the id belongs to; non-matching rows create no edge.
    """
    result: list[dict[str, Any]] = []
    for a in assignments:
        result.append(
            {
                **a,
                "principal_id": account_scoped_id(account_id, str(a["principal_id"])),
            }
        )
    return result


@timeit
def load_assignments(
    neo4j_session: neo4j.Session,
    assignments: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    if not assignments:
        return
    for rel in _ASSIGNMENT_RELS:
        load_matchlinks(
            neo4j_session,
            rel,
            assignments,
            lastupdated=update_tag,
            _sub_resource_label="DatabricksAccount",
            _sub_resource_id=account_id,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, account_id: str, update_tag: int) -> None:
    for rel in _ASSIGNMENT_RELS:
        GraphJob.from_matchlink(
            rel,
            "DatabricksAccount",
            account_id,
            update_tag,
        ).run(neo4j_session)
