import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.grant import DatabricksGroupGrantRel
from cartography.models.databricks.grant import DatabricksServicePrincipalGrantRel
from cartography.models.databricks.grant import DatabricksUserGrantRel
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps a securable node label to its Unity Catalog permissions API path segment.
_SECURABLE_TYPE_BY_LABEL = {
    "DatabricksMetastore": "metastore",
    "DatabricksCatalog": "catalog",
    "DatabricksSchema": "schema",
    "DatabricksTable": "table",
    "DatabricksVolume": "volume",
    "DatabricksFunction": "function",
    "DatabricksConnection": "connection",
    "DatabricksStorageCredential": "storage_credential",
    "DatabricksExternalLocation": "external_location",
    "DatabricksRegisteredModel": "registered_model",
}


def _is_expected_ungrantable(securable: dict[str, Any]) -> bool:
    """Return True for a securable known to reject grant-listing with HTTP 400.

    The only structurally non-grantable securable the module ingests is a
    ``registered_model`` in the Databricks-managed ``system`` catalog (e.g.
    ``system.ai.*``): it has no HAS_PRIVILEGE edges, so skipping it is safe and
    does not require blocking grant cleanup. Any other 400 might be a genuinely
    grantable catalog / schema / table that already holds edges, so it must be
    treated as an incomplete read instead (see ``get``).

    Its ``full_name`` is the three-level UC name ``catalog.schema.model``, so the
    catalog is the first dotted component.
    """
    if securable["securable_type"] != "registered_model":
        return False
    full_name = securable["full_name"] or ""
    return full_name.split(".", 1)[0] == "system"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> bool:
    """Load HAS_PRIVILEGE edges and report whether every securable was read.

    Returns ``complete``: False when a securable that may hold grants was
    skipped (403/404), so the caller can skip the whole-workspace grant cleanup
    rather than deleting still-valid edges for the unread securable.
    """
    securables = get_securables(neo4j_session, workspace_id)
    grants, complete = get(api_session, securables)
    principals = get_principals(neo4j_session, workspace_id)
    grants = resolve_principals(grants, principals)
    load_grants(
        neo4j_session, grants, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    return complete


@timeit
def get_principals(neo4j_session: neo4j.Session, workspace_id: str) -> dict[str, str]:
    """Map each workspace principal's UC name to its scoped node id.

    UC reports grant principals by name (user_name / group display name / SP
    application id); resolving them against *this workspace's* principals keeps
    a shared name across workspaces from matching the wrong node.
    """
    # Key each principal by the exact field UC uses in grants: user_name for
    # users, display_name for groups, application_id for service principals (a
    # service principal also has a display_name, so coalesce would mis-key it).
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(p)
    WHERE p:DatabricksUser OR p:DatabricksGroup OR p:DatabricksServicePrincipal
    RETURN p.id AS id,
           CASE
               WHEN p:DatabricksServicePrincipal THEN p.application_id
               WHEN p:DatabricksGroup THEN p.display_name
               ELSE p.user_name
           END AS name
    """
    result = neo4j_session.run(query, workspace_id=workspace_id)
    principals: dict[str, str] = {}
    for record in result:
        if record["name"] and record["id"]:
            principals[record["name"]] = record["id"]
    return principals


def resolve_principals(
    grants: list[dict[str, Any]], principals: dict[str, str]
) -> list[dict[str, Any]]:
    """Attach the scoped principal node id to each grant, dropping unmatched ones.

    Grants to principals not ingested in this workspace (e.g. account-level
    pseudo-groups like ``account users``) have no node to point at and are
    dropped.
    """
    resolved: list[dict[str, Any]] = []
    for grant in grants:
        principal_id = principals.get(grant["principal"])
        if principal_id is None:
            continue
        resolved.append({**grant, "principal_id": principal_id})
    return resolved


@timeit
def get_securables(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[dict[str, Any]]:
    """Read the grantable UC securables already loaded for this workspace.

    Grants are read straight from the graph so this sync does not depend on the
    ordering of the catalog/schema/table/... syncs that populate it.
    """
    # The permissions endpoint keys most securables by full_name, but metastores
    # by metastore id and storage credentials / external locations by bare name.
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(n:DatabricksSecurable)
    WITH n, [l IN labels(n) WHERE l IN $labels][0] AS label
    WHERE label IS NOT NULL
    RETURN n.id AS id,
           label,
           CASE label
               WHEN 'DatabricksMetastore' THEN n.metastore_id
               WHEN 'DatabricksStorageCredential' THEN n.name
               WHEN 'DatabricksExternalLocation' THEN n.name
               ELSE n.full_name
           END AS full_name
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
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch privilege assignments for each securable.

    Returns ``(grants, complete)``. Each grant is one row per (principal,
    securable): the principal string as UC reports it (username / group name /
    SP application id) plus the securable node id, so a downstream MatchLink
    resolves it to the right principal node. ``complete`` is False when a
    securable that may hold grants was skipped, so the caller can skip the
    whole-workspace cleanup rather than deleting the unrefreshed edges.
    """
    grants: list[dict[str, Any]] = []
    complete = True
    for s in securables:
        uri = (
            f"/api/2.1/unity-catalog/permissions/"
            f"{s['securable_type']}/{s['full_name']}"
        )
        try:
            # Paginate: the permissions endpoint can return a next_page_token
            # (and even empty pages), so a single GET would silently truncate
            # large grant sets and cleanup would then drop the missing edges.
            assignments = api_session.uc_list(
                uri,
                "privilege_assignments",
                params={"max_results": 0},
            )
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            # A `system`-catalog registered_model (e.g. system.ai.*) is the only
            # securable observed to reject grant-listing with 400. It is
            # structurally non-grantable and so has no HAS_PRIVILEGE edges: skip
            # it and keep the read complete (letting cleanup run cannot delete
            # anything valid). Any OTHER 400 is a real BAD_REQUEST (a malformed
            # path or an API-contract change) that would otherwise be swallowed
            # and silently disable cleanup, so it is not skippable and must
            # abort. A 403/404 securable may still hold grants we could not read
            # (403) or vanished mid-sync (404); skip it but flag the read
            # incomplete so the caller skips the whole-workspace cleanup rather
            # than deleting still-valid edges.
            if status == 400 and _is_expected_ungrantable(s):
                logger.warning(
                    "Skipping grants for %s %s: %s",
                    s["securable_type"],
                    s["full_name"],
                    e,
                )
                continue
            skip_or_raise_http(e, 403, 404)
            complete = False
            logger.warning(
                "Skipping grants for %s %s: %s",
                s["securable_type"],
                s["full_name"],
                e,
            )
            continue
        for assignment in assignments:
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
    return grants, complete


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
def cleanup(neo4j_session: neo4j.Session, workspace_id: str, update_tag: int) -> None:
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
