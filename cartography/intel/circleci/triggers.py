import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.models.circleci.trigger import CircleCITriggerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    pipelines: list[dict[str, Any]],
) -> None:
    project_id = common_job_parameters["PROJECT_ID"]
    triggers: list[dict[str, Any]] = []
    for pipeline in pipelines:
        raw = get(
            api_session,
            common_job_parameters["BASE_URL"],
            project_id,
            pipeline["id"],
        )
        triggers.extend(transform(raw, pipeline["id"]))
    load_triggers(
        neo4j_session,
        triggers,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    # Cleanup once per project, after every definition's triggers are loaded.
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    pipeline_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/projects/{project_id}/pipeline-definitions/{pipeline_id}/triggers",
    )


def transform(
    raw: list[dict[str, Any]],
    pipeline_id: str,
) -> list[dict[str, Any]]:
    triggers = []
    for item in raw:
        event_source = item.get("event_source") or {}
        schedule = event_source.get("schedule") or {}
        triggers.append(
            {
                "id": item["id"],
                "event_name": item.get("event_name"),
                "description": item.get("description"),
                "event_preset": item.get("event_preset"),
                "event_source_provider": event_source.get("provider"),
                "cron_expression": schedule.get("cron_expression"),
                "checkout_ref": item.get("checkout_ref"),
                "config_ref": item.get("config_ref"),
                "disabled": item.get("disabled"),
                "pipeline_id": pipeline_id,
            }
        )
    return triggers


@timeit
def load_triggers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCITriggerSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCITriggerSchema(), common_job_parameters).run(
        neo4j_session,
    )
