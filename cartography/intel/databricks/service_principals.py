from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.service_principal import (
    DatabricksServicePrincipalSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    sps = get(api_session)
    transformed = transform(sps, workspace_id)
    load_service_principals(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.scim_list("/api/2.0/preview/scim/v2/ServicePrincipals")


@timeit
def transform(sps: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for sp in sps:
        scim_id = sp["id"]
        result.append(
            {
                "id": scoped_id(workspace_id, scim_id),
                "scim_id": scim_id,
                "application_id": sp.get("applicationId"),
                "display_name": sp.get("displayName"),
                "external_id": sp.get("externalId"),
                "active": sp.get("active"),
                "group_ids": [
                    scoped_id(workspace_id, g["value"])
                    for g in (sp.get("groups") or [])
                    if g.get("value")
                ],
            }
        )
    return result


@timeit
def load_service_principals(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksServicePrincipalSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksServicePrincipalSchema(), common_job_parameters
    ).run(neo4j_session)
