import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.project import VercelProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    projects = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    transform(projects)
    load_projects(
        neo4j_session,
        projects,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return projects


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v9/projects",
        "projects",
        team_id,
    )


def transform(projects: list[dict[str, Any]]) -> None:
    """
    Flatten the deployment-protection objects onto each project, in place.

    `ssoProtection` and `passwordProtection` are nested objects, which the loader cannot
    store, and only their `deploymentType` is of interest. `passwordProtection` also carries
    the password itself, so flattening rather than storing the object is what keeps that
    secret out of the graph. `trustedSources` is reduced to whether an IP allowlist exists.
    """
    for project in projects:
        sso = project.get("ssoProtection") or {}
        password = project.get("passwordProtection") or {}
        project["sso_protection_deployment_type"] = sso.get("deploymentType")
        project["password_protection_deployment_type"] = password.get("deploymentType")
        project["has_trusted_sources"] = bool(project.get("trustedSources"))


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelProjectSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )
