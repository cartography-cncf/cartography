from __future__ import annotations

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.openai.util import paginated_get
from cartography.models.openai.skill import OpenAISkillSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
) -> None:
    skills = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    load_skills(
        neo4j_session,
        skills,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/skills",
            timeout=_TIMEOUT,
        )
    )


@timeit
def load_skills(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d OpenAI Skill into Neo4j.", len(data))
    load(
        neo4j_session,
        OpenAISkillSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OpenAISkillSchema(), common_job_parameters).run(
        neo4j_session
    )
