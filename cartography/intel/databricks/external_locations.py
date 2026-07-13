from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import parse_storage_url
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.external_location import (
    DatabricksExternalLocationSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    locations = get(api_session)
    transformed = transform(locations)
    load_external_locations(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list(
        "/api/2.1/unity-catalog/external-locations", "external_locations"
    )


@timeit
def transform(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for loc in locations:
        name = loc["name"]
        if not name:
            raise ValueError("Databricks external location returned with empty name")
        metastore_id = loc["metastore_id"]
        scheme, bucket = parse_storage_url(loc.get("url"))
        result.append(
            {
                # Fall back to a metastore-scoped id (never a bare name that
                # could collide across metastores) when the API id is missing.
                "id": loc.get("id") or uc_id(metastore_id, name),
                "external_location_id": loc.get("id"),
                "name": name,
                "metastore_id": metastore_id,
                "url": loc.get("url"),
                "credential_id": loc.get("credential_id"),
                "credential_name": loc.get("credential_name"),
                "read_only": loc.get("read_only"),
                "isolation_mode": loc.get("isolation_mode"),
                "fallback": loc.get("fallback"),
                "owner": loc.get("owner"),
                "comment": loc.get("comment"),
                "created_at": epoch_ms_to_datetime(loc.get("created_at")),
                "updated_at": epoch_ms_to_datetime(loc.get("updated_at")),
                "s3_bucket": bucket if scheme in ("s3", "s3a") else None,
                "gcs_bucket": bucket if scheme == "gs" else None,
            }
        )
    return result


@timeit
def load_external_locations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksExternalLocationSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksExternalLocationSchema(), common_job_parameters
    ).run(neo4j_session)
