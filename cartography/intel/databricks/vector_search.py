import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.vector_search import (
    DatabricksVectorSearchEndpointSchema,
)
from cartography.models.databricks.vector_search import (
    DatabricksVectorSearchIndexSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    endpoints = get_endpoints(api_session)
    indexes = get_indexes(api_session, endpoints)
    t_endpoints = transform_endpoints(endpoints, workspace_id)
    t_indexes = transform_indexes(indexes, workspace_id, metastore_id)
    load_vector_search(
        neo4j_session,
        t_endpoints,
        t_indexes,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get_endpoints(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.0/vector-search/endpoints", "endpoints")


@timeit
def get_indexes(
    api_session: DatabricksWorkspaceClient, endpoints: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    indexes: list[dict[str, Any]] = []
    for e in endpoints:
        name = e.get("name")
        if not name:
            continue
        try:
            indexes.extend(
                api_session.uc_list(
                    "/api/2.0/vector-search/indexes",
                    "vector_indexes",
                    params={"endpoint_name": name},
                )
            )
        except requests.HTTPError as ex:
            # An endpoint deleted mid-sync yields 404; skip it. Any other error
            # must abort so cleanup does not drop still-valid index nodes.
            skip_or_raise_http(ex, 404)
            logger.warning(
                "Skipping vector search indexes for deleted endpoint %s: %s",
                name,
                ex,
            )
    return indexes


@timeit
def transform_endpoints(
    endpoints: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for e in endpoints:
        name = e["name"]
        if not name:
            raise ValueError("Databricks vector search endpoint returned empty name")
        status = e.get("endpoint_status") or {}
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "endpoint_id": e.get("id"),
                "name": name,
                "endpoint_type": e.get("endpoint_type"),
                "state": status.get("state"),
                "num_indexes": e.get("num_indexes"),
                "creator": e.get("creator"),
                "created_at": epoch_ms_to_datetime(e.get("creation_timestamp")),
                "last_updated_at": epoch_ms_to_datetime(
                    e.get("last_updated_timestamp")
                ),
            }
        )
    return result


@timeit
def transform_indexes(
    indexes: list[dict[str, Any]], workspace_id: str, metastore_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for idx in indexes:
        name = idx["name"]
        if not name:
            raise ValueError("Databricks vector search index returned empty name")
        delta_spec = idx.get("delta_sync_index_spec") or {}
        source_table = delta_spec.get("source_table")
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "name": name,
                "endpoint_name": idx.get("endpoint_name"),
                "endpoint_id_scoped": (
                    scoped_id(workspace_id, idx["endpoint_name"])
                    if idx.get("endpoint_name")
                    else None
                ),
                "index_type": idx.get("index_type"),
                "primary_key": idx.get("primary_key"),
                "source_table": source_table,
                # Metastore-scoped id so the SOURCED_FROM edge cannot match a
                # same-named table from another metastore.
                "source_table_id": (
                    uc_id(metastore_id, source_table) if source_table else None
                ),
                "creator": idx.get("creator"),
            }
        )
    return result


@timeit
def load_vector_search(
    neo4j_session: neo4j.Session,
    endpoints: list[dict[str, Any]],
    indexes: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksVectorSearchEndpointSchema(),
        endpoints,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )
    load(
        neo4j_session,
        DatabricksVectorSearchIndexSchema(),
        indexes,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksVectorSearchIndexSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DatabricksVectorSearchEndpointSchema(), common_job_parameters
    ).run(neo4j_session)
