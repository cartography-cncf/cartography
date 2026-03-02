import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.member import SentryUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    org_id: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    base_url: str,
    teams: list[dict[str, Any]],
) -> None:
    raw_members = get(api_session, base_url, org_slug)
    transformed = transform(raw_members, teams)
    load_members(neo4j_session, transformed, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated_results(
        api_session,
        f"{base_url}/organizations/{org_slug}/members/",
    )


@timeit
def transform(
    raw_members: list[dict[str, Any]],
    teams: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    team_slug_to_id = {t["slug"]: t["id"] for t in teams}
    result: list[dict[str, Any]] = []
    for member in raw_members:
        m = member.copy()
        m["id"] = member["id"]
        # Extract user details if the member has accepted
        user = member.get("user") or {}
        m["has2fa"] = user.get("has2fa")
        # Resolve team slugs to team IDs
        team_slugs = [
            r.get("teamSlug") for r in member.get("teamRoles", []) if r.get("teamSlug")
        ]
        m["team_ids"] = [team_slug_to_id[s] for s in team_slugs if s in team_slug_to_id]
        result.append(m)
    return result


def load_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d SentryUser(s) into Neo4j.", len(data))
    load(
        neo4j_session,
        SentryUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentryUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
