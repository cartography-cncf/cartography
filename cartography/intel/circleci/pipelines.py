import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.pipeline import CircleCIPipelineSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    project_id = common_job_parameters["PROJECT_ID"]
    raw = get(api_session, common_job_parameters["BASE_URL"], project_id)
    pipelines = transform(raw)
    load_pipelines(
        neo4j_session,
        pipelines,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return pipelines


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> list[dict[str, Any]]:
    # Pipeline "definitions" endpoint - the config/source binding, not runs.
    return paginated_get(
        api_session,
        f"{base_url}/projects/{project_id}/pipeline-definitions",
    )


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pipelines = []
    for item in raw:
        config_source = item.get("config_source") or {}
        checkout_source = item.get("checkout_source") or {}
        # repo is an object {full_name, external_id}, not a scalar - flatten it
        # so it doesn't land in Neo4j as a map (which would fail ingestion).
        config_repo = config_source.get("repo") or {}
        checkout_repo = checkout_source.get("repo") or {}
        pipelines.append(
            {
                "id": item["id"],
                "name": item.get("name"),
                "description": item.get("description"),
                "created_at": parse_iso(item.get("created_at")),
                "config_source_provider": config_source.get("provider"),
                "config_source_repo_full_name": config_repo.get("full_name"),
                "config_source_repo_external_id": config_repo.get("external_id"),
                "config_source_file_path": config_source.get("file_path"),
                "checkout_source_provider": checkout_source.get("provider"),
                "checkout_source_repo_full_name": checkout_repo.get("full_name"),
                "checkout_source_repo_external_id": checkout_repo.get("external_id"),
            }
        )
    return pipelines


@timeit
def load_pipelines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIPipelineSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIPipelineSchema(), common_job_parameters).run(
        neo4j_session,
    )
