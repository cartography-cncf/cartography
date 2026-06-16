import logging
from collections import defaultdict
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.intel.circleci.util import paginated_get
from cartography.models.circleci.project import CircleCIProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# The pipeline feed returns the most recently-built projects (≈250) you follow
# in an org; cap pages so a busy org doesn't page forever during discovery.
_MAX_DISCOVERY_PAGES = 5


@timeit
def discover_project_slugs(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> set[str]:
    """
    Enumerate project slugs for an org. API v2 has no list-projects endpoint, so
    we derive slugs from the pipeline feed (GET /pipeline?org-slug=...), which
    surfaces project_slug for recently-built projects you follow. Combine with
    any operator-configured slugs for full coverage.
    """
    pipelines = paginated_get(
        api_session,
        f"{base_url}/pipeline",
        params={"org-slug": org_slug},
        max_pages=_MAX_DISCOVERY_PAGES,
    )
    return {p["project_slug"] for p in pipelines if p.get("project_slug")}


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
