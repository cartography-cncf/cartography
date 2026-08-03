from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get_by_page
from cartography.models.anthropic.skill import AnthropicSkillSchema
from cartography.models.anthropic.skill import AnthropicSkillVersionSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Sent per request rather than on the session: other Anthropic betas are mutually
# exclusive with each other.
_BETA_HEADERS = {"anthropic-beta": "skills-2025-10-02"}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    skills = get(api_session, common_job_parameters["BASE_URL"])
    versions: list[dict[str, Any]] = []
    for skill in skills:
        for version in get_skill_versions(
            api_session,
            common_job_parameters["BASE_URL"],
            skill["id"],
        ):
            versions.append({**version, "skill_id": skill["id"]})
    load_skills(
        neo4j_session,
        skills,
        common_job_parameters["WORKSPACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_skill_versions(
        neo4j_session,
        versions,
        common_job_parameters["WORKSPACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/skills",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


@timeit
def get_skill_versions(
    api_session: requests.Session,
    base_url: str,
    skill_id: str,
) -> list[dict[str, Any]]:
    return paginated_get_by_page(
        api_session,
        f"{base_url}/skills/{skill_id}/versions",
        timeout=_TIMEOUT,
        headers=_BETA_HEADERS,
    )


@timeit
def load_skills(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicSkillSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def load_skill_versions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    WORKSPACE_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicSkillVersionSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=WORKSPACE_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Versions before skills: they hang off the skills.
    GraphJob.from_node_schema(AnthropicSkillVersionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AnthropicSkillSchema(), common_job_parameters).run(
        neo4j_session
    )
