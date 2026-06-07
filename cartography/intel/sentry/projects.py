from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.project import SentryProjectSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    org_id: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    base_url: str,
) -> list[dict[str, Any]]:
    raw_projects = get(api_session, base_url, org_slug)
    transformed = transform(raw_projects)
    load_projects(neo4j_session, transformed, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return transformed


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated_results(
        api_session,
        f"{base_url}/organizations/{org_slug}/projects/",
    )


@timeit
def transform(raw_projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for project in raw_projects:
        p = project.copy()
        p["id"] = project["id"]
        p["date_created"] = project.get("dateCreated")
        p["first_event"] = project.get("firstEvent")
        p["team_ids"] = [t["id"] for t in project.get("teams", [])]
        result.append(p)
    return result


def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentryProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentryProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )
