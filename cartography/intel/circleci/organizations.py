import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.models.circleci.organization import CircleCIOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    raw = get(api_session, common_job_parameters["BASE_URL"])
    orgs = transform(raw)
    load_organizations(neo4j_session, orgs, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return orgs


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    # /me/collaborations returns a bare JSON array, not a paginated envelope.
    req = api_session.get(f"{base_url}/me/collaborations", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    orgs = []
    for org in raw:
        vcs_type = org.get("vcs_type")
        slug = org.get("slug")
        # Slugs look like "gh/acme"; the GitHub org login is the part after the
        # prefix. Only derive it for GitHub-backed orgs so we don't mis-match.
        vcs_login = None
        if vcs_type == "github" and slug and "/" in slug:
            vcs_login = slug.split("/", 1)[1]
        orgs.append(
            {
                "id": org["id"],
                "name": org.get("name"),
                "slug": slug,
                "vcs_type": vcs_type,
                "avatar_url": org.get("avatar_url"),
                "vcs_login": vcs_login,
            }
        )
    return orgs


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIOrganizationSchema(), common_job_parameters).run(
        neo4j_session
    )
