import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.permission import DatabricksGroupPermissionRel
from cartography.models.databricks.permission import (
    DatabricksServicePrincipalPermissionRel,
)
from cartography.models.databricks.permission import DatabricksUserPermissionRel
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps an ACL-bearing node label to the permissions API path segment and the
# node property that holds the API-native object id (the id the permissions
# endpoint keys the object by, which is NOT the workspace-scoped node id). Read
# straight from each node's intel transform: clusters key by cluster_id, jobs by
# job_id, apps / serving endpoints by name, and so on.
_ACL_OBJECT_BY_LABEL = {
    "DatabricksCluster": ("clusters", "cluster_id"),
    "DatabricksClusterPolicy": ("cluster-policies", "policy_id"),
    "DatabricksInstancePool": ("instance-pools", "instance_pool_id"),
    "DatabricksJob": ("jobs", "job_id"),
    "DatabricksPipeline": ("pipelines", "pipeline_id"),
    "DatabricksSqlWarehouse": ("sql/warehouses", "warehouse_id"),
    "DatabricksServingEndpoint": ("serving-endpoints", "endpoint_id"),
    "DatabricksApp": ("apps", "name"),
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    objects = get_objects(neo4j_session, workspace_id)
    scopes = get_secret_scopes(neo4j_session, workspace_id)
    object_permissions, objects_complete = get(api_session, objects)
    scope_permissions, scopes_complete = get_secret_scope_acls(api_session, scopes)
    permissions = object_permissions + scope_permissions
    principals = get_principals(neo4j_session, workspace_id)
    permissions = resolve_principals(permissions, principals)
    load_permissions(
        neo4j_session, permissions, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    # Only clean up when every object's ACL was read this run. A 403/404 on one
    # object means its edges were not refreshed, so a whole-workspace MatchLink
    # cleanup would delete still-valid HAS_PERMISSION edges for it; skip cleanup
    # and let a fully successful run reconcile the stale edges instead.
    if objects_complete and scopes_complete:
        cleanup(neo4j_session, workspace_id, common_job_parameters["UPDATE_TAG"])
    else:
        logger.warning(
            "Databricks permissions were partially read for workspace %s; "
            "skipping HAS_PERMISSION cleanup to avoid deleting valid edges.",
            workspace_id,
        )


@timeit
def get_principals(neo4j_session: neo4j.Session, workspace_id: str) -> dict[str, str]:
    """Map each workspace principal's ACL name to its scoped node id.

    The permissions API reports ACL principals by name (user_name / group
    display name / SP application id); resolving them against *this workspace's*
    principals keeps a shared name across workspaces from matching the wrong
    node. Mirrors grants.get_principals.
    """
    # Key each principal by the exact field the permissions API uses: user_name
    # for users, display_name for groups, application_id for service principals
    # (an SP also has a display_name, so coalesce would mis-key it).
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
    permissions: list[dict[str, Any]], principals: dict[str, str]
) -> list[dict[str, Any]]:
    """Attach the scoped principal node id to each ACL, dropping unmatched ones.

    ACLs granted to principals not ingested in this workspace (e.g. the built-in
    ``admins`` pseudo-group or an account-level principal) have no node to point
    at and are dropped.
    """
    resolved: list[dict[str, Any]] = []
    for perm in permissions:
        principal_id = principals.get(perm["principal"])
        if principal_id is None:
            continue
        resolved.append({**perm, "principal_id": principal_id})
    return resolved


@timeit
def get_objects(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[dict[str, Any]]:
    """Read the ACL-bearing workspace objects already loaded for this workspace.

    Objects are read straight from the graph so this sync does not depend on the
    ordering of the cluster / job / pipeline / ... syncs that populate them. Each
    row carries the node id (MatchLink target) plus the API-native object ref the
    permissions endpoint keys by.
    """
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(n:DatabricksAclObject)
    WITH n, [l IN labels(n) WHERE l IN $labels][0] AS label
    WHERE label IS NOT NULL
    RETURN n.id AS id,
           label,
           CASE label
               WHEN 'DatabricksCluster' THEN n.cluster_id
               WHEN 'DatabricksClusterPolicy' THEN n.policy_id
               WHEN 'DatabricksInstancePool' THEN n.instance_pool_id
               WHEN 'DatabricksJob' THEN n.job_id
               WHEN 'DatabricksPipeline' THEN n.pipeline_id
               WHEN 'DatabricksSqlWarehouse' THEN n.warehouse_id
               WHEN 'DatabricksServingEndpoint' THEN n.endpoint_id
               ELSE n.name
           END AS object_ref
    """
    result = neo4j_session.run(
        query,
        workspace_id=workspace_id,
        labels=list(_ACL_OBJECT_BY_LABEL.keys()),
    )
    objects: list[dict[str, Any]] = []
    for record in result:
        label = record["label"]
        if not label or not record["object_ref"]:
            continue
        object_type, _ = _ACL_OBJECT_BY_LABEL[label]
        objects.append(
            {
                "id": record["id"],
                "object_ref": record["object_ref"],
                "object_type": object_type,
            }
        )
    return objects


@timeit
def get_secret_scopes(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[dict[str, Any]]:
    """Read the secret scopes already loaded for this workspace.

    Secret scope ACLs live on a different endpoint keyed by scope name, so they
    are collected separately from the generic permissions objects.
    """
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(s:DatabricksSecretScope)
    RETURN s.id AS id, s.name AS name
    """
    result = neo4j_session.run(query, workspace_id=workspace_id)
    scopes: list[dict[str, Any]] = []
    for record in result:
        if record["id"] and record["name"]:
            scopes.append({"id": record["id"], "name": record["name"]})
    return scopes


@timeit
def get(
    api_session: DatabricksWorkspaceClient, objects: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch the ACL of each workspace object via the permissions endpoint.

    Returns ``(permissions, complete)`` where each permission is one row per
    (principal, object): the principal string as the API reports it (user_name /
    group_name / service_principal_name) plus the object node id, so a downstream
    MatchLink resolves it to the right principal node. ``complete`` is False when
    any object's ACL was skipped (403/404), so the caller can skip cleanup rather
    than delete the unrefreshed edges.
    """
    permissions: list[dict[str, Any]] = []
    complete = True
    for obj in objects:
        uri = f"/api/2.0/permissions/{obj['object_type']}/{obj['object_ref']}"
        try:
            response = api_session.get(uri)
        except requests.HTTPError as e:
            # An object the caller can't read the ACL on (403) or that vanished
            # mid-sync (404) is skippable; any other error must abort so the
            # permission cleanup does not drop still-valid HAS_PERMISSION edges.
            skip_or_raise_http(e, 403, 404)
            complete = False
            logger.warning(
                "Skipping permissions for %s %s: %s",
                obj["object_type"],
                obj["object_ref"],
                e,
            )
            continue
        for entry in response.get("access_control_list", []) or []:
            principal = (
                entry.get("user_name")
                or entry.get("group_name")
                or entry.get("service_principal_name")
            )
            if not principal:
                continue
            # Collapse all_permissions to the distinct permission_level values;
            # a principal can appear once with several (direct + inherited)
            # levels, and the level names are what access-path analysis reasons
            # about.
            levels = sorted(
                {
                    p.get("permission_level")
                    for p in entry.get("all_permissions", []) or []
                    if p.get("permission_level")
                }
            )
            if not levels:
                continue
            permissions.append(
                {
                    "principal": principal,
                    "object_id": obj["id"],
                    "permission_level": levels,
                    "object_type": obj["object_type"],
                }
            )
    return permissions, complete


@timeit
def get_secret_scope_acls(
    api_session: DatabricksWorkspaceClient, scopes: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch each secret scope's ACL via the secrets endpoint.

    Secret scopes use ``/api/2.0/secrets/acls/list`` (keyed by scope name), whose
    items carry ``principal`` + a single ``permission`` (READ | WRITE | MANAGE)
    rather than the ``access_control_list`` shape the permissions endpoint uses.
    Returns ``(permissions, complete)``; ``complete`` is False when any scope's
    ACL was skipped (403/404) so the caller can skip cleanup.
    """
    permissions: list[dict[str, Any]] = []
    complete = True
    for scope in scopes:
        try:
            response = api_session.get(
                "/api/2.0/secrets/acls/list", params={"scope": scope["name"]}
            )
        except requests.HTTPError as e:
            skip_or_raise_http(e, 403, 404)
            complete = False
            logger.warning("Skipping secret scope ACL for %s: %s", scope["name"], e)
            continue
        for item in response.get("items", []) or []:
            principal = item.get("principal")
            permission = item.get("permission")
            if not principal or not permission:
                continue
            permissions.append(
                {
                    "principal": principal,
                    "object_id": scope["id"],
                    "permission_level": [permission],
                    "object_type": "secret-scope",
                }
            )
    return permissions, complete


@timeit
def load_permissions(
    neo4j_session: neo4j.Session,
    permissions: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    if not permissions:
        return
    # A principal name resolves to exactly one of user / group / service
    # principal, so feeding every row to all three MatchLinks lets the matchers
    # decide; non-matching rows simply create no edge.
    for rel in (
        DatabricksUserPermissionRel(),
        DatabricksGroupPermissionRel(),
        DatabricksServicePrincipalPermissionRel(),
    ):
        load_matchlinks(
            neo4j_session,
            rel,
            permissions,
            lastupdated=update_tag,
            _sub_resource_label="DatabricksWorkspace",
            _sub_resource_id=workspace_id,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, workspace_id: str, update_tag: int) -> None:
    for rel in (
        DatabricksUserPermissionRel(),
        DatabricksGroupPermissionRel(),
        DatabricksServicePrincipalPermissionRel(),
    ):
        GraphJob.from_matchlink(
            rel,
            "DatabricksWorkspace",
            workspace_id,
            update_tag,
        ).run(neo4j_session)
