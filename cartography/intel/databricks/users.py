from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.user import DatabricksUserSchema
from cartography.util import timeit


def _primary_email(emails: list[dict[str, Any]] | None) -> str | None:
    if not emails:
        return None
    for entry in emails:
        if entry.get("primary"):
            return entry.get("value")
    return emails[0].get("value")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(api_session)
    transformed = transform(users, workspace_id)
    load_users(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.scim_list("/api/2.0/preview/scim/v2/Users")


@timeit
def transform(users: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for u in users:
        scim_id = u["id"]
        result.append(
            {
                "id": scoped_id(workspace_id, scim_id),
                "scim_id": scim_id,
                "user_name": u.get("userName"),
                "display_name": u.get("displayName"),
                "external_id": u.get("externalId"),
                "active": u.get("active"),
                "email": _primary_email(u.get("emails")),
                "group_ids": [
                    scoped_id(workspace_id, g["value"])
                    for g in (u.get("groups") or [])
                    if g.get("value")
                ],
            }
        )
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksUserSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksUserSchema(), common_job_parameters).run(
        neo4j_session
    )
