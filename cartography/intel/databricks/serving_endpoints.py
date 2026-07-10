from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.served_entity import DatabricksServedEntitySchema
from cartography.models.databricks.serving_endpoint import (
    DatabricksServingEndpointSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    endpoints = get(api_session)
    transformed_endpoints = transform_endpoints(endpoints, workspace_id)
    transformed_entities = transform_served_entities(endpoints, workspace_id)
    load_endpoints(
        neo4j_session,
        transformed_endpoints,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    load_served_entities(
        neo4j_session,
        transformed_entities,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List serving endpoints. The endpoint returns the full set in one response."""
    return api_session.get("/api/2.0/serving-endpoints").get("endpoints", []) or []


@timeit
def transform_endpoints(
    endpoints: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for e in endpoints:
        name = e.get("name")
        if not name:
            raise ValueError("Databricks serving endpoint returned with empty name")
        state = e.get("state") or {}
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "name": name,
                "endpoint_type": e.get("endpoint_type"),
                "task": e.get("task"),
                "state_ready": state.get("ready"),
                "state_config_update": state.get("config_update"),
                "permission_level": e.get("permission_level"),
                "route_optimized": e.get("route_optimized"),
                "creator": e.get("creator"),
                "creation_timestamp": epoch_ms_to_datetime(e.get("creation_timestamp")),
                "last_updated_timestamp": epoch_ms_to_datetime(
                    e.get("last_updated_timestamp")
                ),
            }
        )
    return result


@timeit
def transform_served_entities(
    endpoints: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    """Flatten each endpoint's served entities into standalone rows.

    Entity ids are ``{workspace}/{endpoint}/{served_name}`` so the same model
    served behind two endpoints stays distinct.
    """
    result: list[dict[str, Any]] = []
    for e in endpoints:
        endpoint_name = e.get("name")
        if not endpoint_name:
            continue
        endpoint_scoped_id = scoped_id(workspace_id, endpoint_name)
        for se in (e.get("config") or {}).get("served_entities", []) or []:
            served_name = se.get("name") or se.get("entity_name")
            if not served_name:
                continue
            foundation = se.get("foundation_model") or {}
            external = se.get("external_model") or {}
            result.append(
                {
                    "id": f"{endpoint_scoped_id}/{served_name}",
                    "served_name": served_name,
                    "endpoint_name": endpoint_name,
                    "endpoint_scoped_id": endpoint_scoped_id,
                    "entity_name": se.get("entity_name"),
                    "entity_type": se.get("type"),
                    "entity_version": se.get("entity_version"),
                    "foundation_model_name": foundation.get("name"),
                    "external_model_provider": external.get("provider"),
                    "external_model_name": external.get("name"),
                }
            )
    return result


@timeit
def load_endpoints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksServingEndpointSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_served_entities(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksServedEntitySchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Served entities hang off endpoints, so purge the children first.
    GraphJob.from_node_schema(
        DatabricksServedEntitySchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DatabricksServingEndpointSchema(), common_job_parameters
    ).run(neo4j_session)
