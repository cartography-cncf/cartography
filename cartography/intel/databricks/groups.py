from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.group import DatabricksGroupSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    groups = get(api_session)
    transformed = transform(groups, workspace_id)
    load_groups(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.scim_list("/api/2.0/preview/scim/v2/Groups")


@timeit
def transform(groups: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    """Flatten SCIM nested-group memberships into parent_group_ids on each group.

    Databricks SCIM exposes group nesting via two paths and only one is
    guaranteed to be populated on any given response:
      - the parent's ``members`` list (with ``$ref: "Groups/..."``), and
      - the child's own ``groups`` list (same shape as Users / SPs).
    Both are consumed and deduplicated so the Group -> Group MEMBER_OF edge
    lands regardless of which side the API fills in.

    Edges to users and service principals are reverse-materialised on those
    nodes via the ``group_ids`` list returned by the SCIM Users /
    ServicePrincipals endpoints.

    Node ids are scoped to the workspace so multi-workspace ingestion does
    not collide on workspace-scoped SCIM ids.
    """
    by_scim_id: dict[str, dict[str, Any]] = {}
    for g in groups:
        scim_id = g["id"]
        by_scim_id[scim_id] = {
            "id": scoped_id(workspace_id, scim_id),
            "scim_id": scim_id,
            "display_name": g.get("displayName"),
            "external_id": g.get("externalId"),
            # set() during accumulation, list() before return so the load layer
            # gets a deterministic, JSON-friendly value.
            "_parent_set": set(),
        }
    for g in groups:
        scim_id = g["id"]
        # Upward: the child group's own ``groups`` field.
        for parent in g.get("groups", []) or []:
            parent_id = parent.get("value")
            if parent_id and parent_id in by_scim_id:
                by_scim_id[scim_id]["_parent_set"].add(
                    scoped_id(workspace_id, parent_id)
                )
        # Downward: the parent group's ``members`` field with $ref="Groups/...".
        for member in g.get("members", []) or []:
            member_id = member.get("value")
            member_ref = member.get("$ref", "") or ""
            if not member_id:
                continue
            if member_ref.startswith("Groups/") and member_id in by_scim_id:
                by_scim_id[member_id]["_parent_set"].add(
                    scoped_id(workspace_id, scim_id)
                )
    result: list[dict[str, Any]] = []
    for entry in by_scim_id.values():
        entry["parent_group_ids"] = sorted(entry.pop("_parent_set"))
        result.append(entry)
    return result


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksGroupSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
