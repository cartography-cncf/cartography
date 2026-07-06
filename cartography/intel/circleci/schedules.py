import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.models.circleci.schedule import CircleCIScheduleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_slug: str,
) -> None:
    raw = get(api_session, common_job_parameters["BASE_URL"], project_slug)
    schedules = transform(raw)
    load_schedules(
        neo4j_session,
        schedules,
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slug: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/project/{project_slug}/schedule",
    )


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    schedules = []
    for item in raw:
        actor = item.get("actor") or {}
        schedules.append(
            {
                "id": item["id"],
                "name": item.get("name"),
                "description": item.get("description"),
                "project_slug": item.get("project_slug"),
                "actor_login": actor.get("login"),
            }
        )
    return schedules


@timeit
def load_schedules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIScheduleSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIScheduleSchema(), common_job_parameters).run(
        neo4j_session,
    )
