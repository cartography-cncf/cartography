import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.registered_model import DatabricksModelVersionSchema
from cartography.models.databricks.registered_model import (
    DatabricksRegisteredModelSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    models = get(api_session, schemas)
    versions = get_versions(api_session, models)
    t_models, t_versions = transform(models, versions)
    load_models(
        neo4j_session,
        t_models,
        t_versions,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(
    api_session: DatabricksWorkspaceClient, schemas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for s in schemas:
        catalog_name = s.get("catalog_name")
        schema_name = s.get("name")
        if not catalog_name or not schema_name:
            continue
        try:
            models.extend(
                api_session.uc_list(
                    "/api/2.1/unity-catalog/models",
                    "registered_models",
                    params={
                        "catalog_name": catalog_name,
                        "schema_name": schema_name,
                    },
                )
            )
        except requests.HTTPError as e:
            # Skip an expected 403 on a system-managed schema; re-raise anything
            # else so cleanup does not run on partial data.
            skip_or_raise_http(e, 403)
            logger.warning(
                "Skipping models for schema %s.%s (permission denied): %s",
                catalog_name,
                schema_name,
                e,
            )
    return models


@timeit
def get_versions(
    api_session: DatabricksWorkspaceClient, models: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    for m in models:
        full_name = m.get("full_name")
        if not full_name:
            continue
        try:
            versions.extend(
                api_session.uc_list(
                    f"/api/2.1/unity-catalog/models/{full_name}/versions",
                    "model_versions",
                )
            )
        except requests.HTTPError as e:
            # A model deleted mid-sync yields 404; skip it. Any other failure
            # must abort so cleanup does not delete still-valid version nodes.
            skip_or_raise_http(e, 404)
            logger.warning("Skipping versions for deleted model %s: %s", full_name, e)
    return versions


@timeit
def transform(
    models: list[dict[str, Any]], versions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    t_models: list[dict[str, Any]] = []
    for m in models:
        metastore_id = m["metastore_id"]
        full_name = m["full_name"]
        if not full_name:
            raise ValueError("Databricks registered model returned empty full_name")
        parent_schema = f"{m['catalog_name']}.{m['schema_name']}"
        t_models.append(
            {
                "id": uc_id(metastore_id, full_name),
                "model_id": m.get("id"),
                "name": m.get("name"),
                "full_name": full_name,
                "catalog_name": m.get("catalog_name"),
                "schema_name": m.get("schema_name"),
                "parent_schema_id": uc_id(metastore_id, parent_schema),
                "metastore_id": metastore_id,
                "owner": m.get("owner"),
                "comment": m.get("comment"),
                "storage_location": m.get("storage_location"),
                "created_at": epoch_ms_to_datetime(m.get("created_at")),
                "updated_at": epoch_ms_to_datetime(m.get("updated_at")),
                "created_by": m.get("created_by"),
                "updated_by": m.get("updated_by"),
            }
        )

    t_versions: list[dict[str, Any]] = []
    for v in versions:
        metastore_id = v["metastore_id"]
        model_full_name = f"{v['catalog_name']}.{v['schema_name']}.{v['model_name']}"
        version = v["version"]
        t_versions.append(
            {
                "id": f"{uc_id(metastore_id, model_full_name)}/{version}",
                "version": version,
                "model_name": v.get("model_name"),
                "model_id": uc_id(metastore_id, model_full_name),
                "metastore_id": metastore_id,
                "status": v.get("status"),
                "source": v.get("source"),
                "run_id": v.get("run_id"),
                "storage_location": v.get("storage_location"),
                "comment": v.get("comment"),
                "created_at": epoch_ms_to_datetime(v.get("created_at")),
                "updated_at": epoch_ms_to_datetime(v.get("updated_at")),
                "created_by": v.get("created_by"),
                "updated_by": v.get("updated_by"),
            }
        )
    return t_models, t_versions


@timeit
def load_models(
    neo4j_session: neo4j.Session,
    models: list[dict[str, Any]],
    versions: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksRegisteredModelSchema(),
        models,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )
    load(
        neo4j_session,
        DatabricksModelVersionSchema(),
        versions,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksModelVersionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DatabricksRegisteredModelSchema(), common_job_parameters
    ).run(neo4j_session)
