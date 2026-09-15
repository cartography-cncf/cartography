import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.deployment import VercelDeploymentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
    protection: dict[str, Any] | None = None,
) -> None:
    deployments = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
        project_id,
    )
    transform(deployments, protection)
    load_deployments(
        neo4j_session,
        deployments,
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
        f"{base_url}/v6/deployments",
        "deployments",
        team_id,
        params={"projectId": project_id, "limit": 100},
    )


def transform(
    deployments: list[dict[str, Any]],
    protection: dict[str, Any] | None = None,
) -> None:
    protection = protection or {}
    for d in deployments:
        d["creator_uid"] = d.get("creator", {}).get("uid")
        d["meta_git_commit_sha"] = d.get("meta", {}).get("githubCommitSha")
        d["meta_git_branch"] = d.get("meta", {}).get("branchAlias")
        exposed = _is_exposed(d, protection)
        d["exposed_internet"] = exposed
        d["exposed_internet_type"] = ["direct"] if exposed else None


# Which deploymentType values of a protection method cover a given deployment. A production
# deployment is not covered by `preview`, and `prod_deployment_urls_and_all_previews` covers
# the generated production deployment URL, which is what VercelDeployment.url holds.
_COVERS_PRODUCTION = frozenset({"all", "prod_deployment_urls_and_all_previews"})
_COVERS_PREVIEW = frozenset({"all", "preview", "prod_deployment_urls_and_all_previews"})


def _is_exposed(deployment: dict[str, Any], protection: dict[str, Any]) -> bool:
    """
    Whether anyone on the internet can reach this deployment's URL.

    A READY deployment answers on its URL unless one of the project's protection methods
    covers it. Which methods cover it depends on whether it is a production or a preview
    deployment, since Vercel scopes both Vercel Authentication and password protection by
    deployment type.

    An unrecognised deploymentType is treated as not covering the deployment, so a value
    Vercel adds later errs towards reporting exposure rather than hiding it.

    Vercel's IP allowlist, `trustedIps`, is not considered: it is absent from the documented
    schema of the projects listing this module reads, so a project relying on it alone is
    reported as exposed. That is the safe direction. `trustedSources` is not a restriction at
    all, see the note in projects.transform.
    """
    if deployment.get("state") != "READY" or not deployment.get("url"):
        return False
    covers = (
        _COVERS_PRODUCTION
        if deployment.get("target") == "production"
        else _COVERS_PREVIEW
    )
    gated = (
        protection.get("sso_protection_deployment_type") in covers
        or protection.get("password_protection_deployment_type") in covers
    )
    return not gated


@timeit
def load_deployments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelDeploymentSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelDeploymentSchema(), common_job_parameters).run(
        neo4j_session,
    )
