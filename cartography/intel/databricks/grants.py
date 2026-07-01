import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.models.databricks.grant import DatabricksGroupGrantRel
from cartography.models.databricks.grant import DatabricksServicePrincipalGrantRel
from cartography.models.databricks.grant import DatabricksUserGrantRel
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps a securable node label to its Unity Catalog permissions API path segment.
_SECURABLE_TYPE_BY_LABEL = {
    "DatabricksCatalog": "catalog",
    "DatabricksSchema": "schema",
    "DatabricksTable": "table",
    "DatabricksVolume": "volume",
    "DatabricksFunction": "function",
    "DatabricksConnection": "connection",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    securables = get_securables(neo4j_session, workspace_id)
    grants = get(api_session, securables)
    load_grants(neo4j_session, grants, workspace_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, workspace_id, common_job_parameters["UPDATE_TAG"])


@timeit
def get_securables(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[dict[str, Any]]:
    """Read the grantable UC securables already loaded for this workspace.

    Grants are read straight from the graph so this sync does not depend on the
    ordering of the catalog/schema/table/... syncs that populate it.
    """
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(n:DatabricksSecurable)
    RETURN n.id AS id,
           n.full_name AS full_name,
           [l IN labels(n) WHERE l IN $labels][0] AS label
    """
    result = neo4j_session.run(
        query,
        workspace_id=workspace_id,
        labels=list(_SECURABLE_TYPE_BY_LABEL.keys()),
    )
    securables: list[dict[str, Any]] = []
    for record in result:
        label = record["label"]
        if not label or not record["full_name"]:
            continue
        securables.append(
            {
                "id": record["id"],
                "full_name": record["full_name"],
                "securable_type": _SECURABLE_TYPE_BY_LABEL[label],
            }
        )
    return securables


@timeit
def get(
    api_session: DatabricksWorkspaceClient, securables: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Fetch privilege assignments for each securable.

    Returns one row per (principal, securable): the principal string as UC
    reports it (username / group name / SP application id) plus the securable
    node id, so a downstream MatchLink resolves it to the right principal node.
    """
    grants: list[dict[str, Any]] = []
    for s in securables:
        uri = (
            f"/api/2.1/unity-catalog/permissions/"
            f"{s['securable_type']}/{s['full_name']}"
        )
        try:
            response = api_session.get(uri)
        except requests.HTTPError as e:
            logger.warning(
                "Failed to fetch grants for %s %s: %s",
                s["securable_type"],
                s["full_name"],
                e,
            )
            continue
        for assignment in response.get("privilege_assignments", []) or []:
            principal = assignment.get("principal")
            privileges = assignment.get("privileges") or []
            if not principal or not privileges:
                continue
            grants.append(
                {
                    "principal": principal,
                    "securable_id": s["id"],
                    "privileges": privileges,
                }
            )
    return grants


@timeit
def load_grants(
    neo4j_session: neo4j.Session,
    grants: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    if not grants:
        return
    # A principal name resolves to exactly one of user / group / service
    # principal, so feeding every row to all three MatchLinks lets the matchers
    # decide; non-matching rows simply create no edge.
    for rel in (
        DatabricksUserGrantRel(),
        DatabricksGroupGrantRel(),
        DatabricksServicePrincipalGrantRel(),
    ):
        load_matchlinks(
            neo4j_session,
            rel,
            grants,
            lastupdated=update_tag,
            _sub_resource_label="DatabricksWorkspace",
            _sub_resource_id=workspace_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, workspace_id: str, update_tag: int
) -> None:
    for rel in (
        DatabricksUserGrantRel(),
        DatabricksGroupGrantRel(),
        DatabricksServicePrincipalGrantRel(),
    ):
        GraphJob.from_matchlink(
            rel,
            "DatabricksWorkspace",
            workspace_id,
            update_tag,
        ).run(neo4j_session)
