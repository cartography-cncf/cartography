import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import get_run_as_principal_index
from cartography.intel.databricks.util import scoped_id
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.pipeline import DatabricksPipelineSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str | None,
    common_job_parameters: dict[str, Any],
) -> None:
    pipelines = get(api_session)
    principals = get_run_as_principal_index(neo4j_session, workspace_id)
    transformed = transform(pipelines, workspace_id, metastore_id, principals)
    load_pipelines(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List pipelines, then fetch each one's spec.

    The list endpoint only returns status fields; the catalog / target schema /
    compute flags live on the per-pipeline detail, so fetch it for each.
    """
    statuses: list[dict[str, Any]] = []
    params: dict[str, Any] = {"max_results": 100}
    seen_tokens: set[str] = set()
    while True:
        response = api_session.get("/api/2.0/pipelines", params=params)
        statuses.extend(response.get("statuses", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks pipelines list repeated page token {next_token!r}; "
                "aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"max_results": 100, "page_token": next_token}

    pipelines: list[dict[str, Any]] = []
    for status in statuses:
        pipeline_id = status.get("pipeline_id")
        if not pipeline_id:
            continue
        try:
            pipelines.append(api_session.get(f"/api/2.0/pipelines/{pipeline_id}"))
        except requests.HTTPError as e:
            # A pipeline deleted mid-sync (404) or one we cannot read (403) is
            # skipped per-resource, matching the other UC modules; anything else
            # aborts so cleanup does not run on partial data.
            skip_or_raise_http(e, 403, 404)
            logger.warning("Skipping pipeline %s: %s", pipeline_id, e)
    return pipelines


@timeit
def transform(
    pipelines: list[dict[str, Any]],
    workspace_id: str,
    metastore_id: str | None,
    principals: dict[str, tuple[str, bool]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for p in pipelines:
        pipeline_id = p.get("pipeline_id")
        if not pipeline_id:
            raise ValueError("Databricks pipeline returned with empty pipeline_id")
        spec = p.get("spec") or {}
        catalog = spec.get("catalog")
        run_as_name = p.get("run_as_user_name")
        resolved = principals.get(run_as_name) if run_as_name else None
        run_as_id, is_sp = resolved if resolved else (None, False)
        result.append(
            {
                "id": scoped_id(workspace_id, pipeline_id),
                "pipeline_id": pipeline_id,
                "name": p.get("name"),
                "state": p.get("state"),
                "creator_user_name": p.get("creator_user_name"),
                "run_as_user_name": run_as_name,
                "run_as_user_id": run_as_id if not is_sp else None,
                "run_as_sp_id": run_as_id if is_sp else None,
                "catalog": catalog,
                # UC pipelines publish to spec.schema; legacy ones to spec.target.
                "target_schema": spec.get("schema") or spec.get("target"),
                "storage": spec.get("storage"),
                "continuous": spec.get("continuous"),
                "development": spec.get("development"),
                "serverless": spec.get("serverless"),
                "photon": spec.get("photon"),
                "edition": spec.get("edition"),
                "channel": spec.get("channel"),
                "pipeline_type": spec.get("pipeline_type"),
                # Only a UC catalog (metastore known) resolves to a catalog node.
                "catalog_scoped_id": (
                    uc_id(metastore_id, catalog) if metastore_id and catalog else None
                ),
            }
        )
    return result


@timeit
def load_pipelines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksPipelineSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksPipelineSchema(), common_job_parameters).run(
        neo4j_session
    )
