import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.models.circleci.project_env_var import CircleCIProjectEnvVarSchema
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
    env_vars = transform(raw, project_slug)
    load_project_env_vars(
        neo4j_session,
        env_vars,
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
        f"{base_url}/project/{project_slug}/envvar",
    )


def transform(
    raw: list[dict[str, Any]],
    project_slug: str,
) -> list[dict[str, Any]]:
    # The API returns only a masked value ("xxxx" + last 4 chars), never the real secret.
    return [
        {
            "id": f"{project_slug}:{item['name']}",
            "name": item["name"],
            "project_slug": project_slug,
            "value": item.get("value"),
        }
        for item in raw
    ]


@timeit
def load_project_env_vars(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIProjectEnvVarSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIProjectEnvVarSchema(), common_job_parameters).run(
        neo4j_session
    )
