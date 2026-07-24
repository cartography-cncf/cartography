from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.environment import DopplerEnvironmentSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project_slugs: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    environments = get(api_session, common_job_parameters["BASE_URL"], project_slugs)
    load_environments(
        neo4j_session,
        environments,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slugs: list[str],
) -> list[dict[str, Any]]:
    environments: list[dict[str, Any]] = []
    for project in project_slugs:
        for env in paginated_get(
            api_session,
            f"{base_url}/environments",
            "environments",
            params={"project": project},
        ):
            env_id = env["id"]
            environments.append(
                {
                    "id": f"{project}/{env_id}",
                    "env_id": env_id,
                    "name": env.get("name"),
                    "project": project,
                    "created_at": env.get("created_at"),
                    "initial_fetch_at": env.get("initial_fetch_at"),
                }
            )
    return environments


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    environments: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerEnvironmentSchema(),
        environments,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerEnvironmentSchema(), common_job_parameters).run(
        neo4j_session
    )
