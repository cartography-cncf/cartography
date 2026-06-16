import logging
from collections import defaultdict
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.models.circleci.project import CircleCIProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_slugs: list[str],
) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for slug in project_slugs:
        raw = get(api_session, common_job_parameters["BASE_URL"], slug)
        projects.append(transform(raw))

    # Group by org so cleanup is scoped per-org and one configured project's
    # cleanup cannot delete a sibling project in the same org.
    by_org: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in projects:
        by_org[project["organization_id"]].append(project)
    for org_id, org_projects in by_org.items():
        load_projects(
            neo4j_session,
            org_projects,
            org_id,
            common_job_parameters["UPDATE_TAG"],
        )
        cleanup(neo4j_session, {**common_job_parameters, "ORG_ID": org_id})
    return projects


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slug: str,
) -> dict[str, Any]:
    req = api_session.get(f"{base_url}/project/{project_slug}", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


def transform(raw: dict[str, Any]) -> dict[str, Any]:
    vcs = raw.get("vcs_info") or {}
    return {
        "id": raw["id"],
        "slug": raw.get("slug"),
        "name": raw.get("name"),
        "organization_name": raw.get("organization_name"),
        "organization_slug": raw.get("organization_slug"),
        "organization_id": raw["organization_id"],
        "vcs_url": vcs.get("vcs_url"),
        "vcs_provider": vcs.get("provider"),
        "default_branch": vcs.get("default_branch"),
    }


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )
