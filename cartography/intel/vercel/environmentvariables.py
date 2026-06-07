import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.environmentvariable import (
    VercelEnvironmentVariableSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
) -> None:
    env_vars = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
        project_id,
    )
    load_environment_variables(
        neo4j_session,
        env_vars,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
    project_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v10/projects/{project_id}/env",
        "envs",
        team_id,
    )


@timeit
def load_environment_variables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelEnvironmentVariableSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        VercelEnvironmentVariableSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
