from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.team import SentryTeamSchema
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
    raw_teams = get(api_session, base_url, org_slug)
    transformed = transform(raw_teams)
    load_teams(neo4j_session, transformed, org_id, update_tag)
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
        f"{base_url}/organizations/{org_slug}/teams/",
    )


@timeit
def transform(raw_teams: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for team in raw_teams:
        t = team.copy()
        t["id"] = team["id"]
        t["date_created"] = team.get("dateCreated")
        result.append(t)
    return result


def load_teams(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentryTeamSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentryTeamSchema(), common_job_parameters).run(
        neo4j_session,
    )
