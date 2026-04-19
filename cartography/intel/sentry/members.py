from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.member import SentryUserSchema
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
    teams: list[dict[str, Any]],
) -> None:
    raw_members = get(api_session, base_url, org_slug)
    team_memberships = _get_team_memberships(api_session, base_url, org_slug, teams)
    transformed = transform(raw_members, team_memberships, teams)
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


def _get_team_memberships(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
    teams: list[dict[str, Any]],
) -> dict[str, list[tuple[str, str]]]:
    """Build a mapping of member_id -> [(team_id, role), ...] by querying each team's members."""
    member_to_teams: dict[str, list[tuple[str, str]]] = {}
    for team in teams:
        team_slug = team["slug"]
        team_id = team["id"]
        team_members = get_paginated_results(
            api_session,
            f"{base_url}/teams/{org_slug}/{team_slug}/members/",
        )
        for tm in team_members:
            member_id = str(tm["id"])
            role = tm.get("teamRole") or "contributor"
            member_to_teams.setdefault(member_id, []).append((team_id, role))
    return member_to_teams


@timeit
def transform(
    raw_members: list[dict[str, Any]],
    team_memberships: dict[str, list[tuple[str, str]]],
    teams: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_team_ids = [t["id"] for t in teams]
    result: list[dict[str, Any]] = []
    for member in raw_members:
        m = member.copy()
        m["id"] = member["id"]
        # Extract user details if the member has accepted
        user = member.get("user") or {}
        m["has2fa"] = user.get("has2fa")
        # Owners are implicit admins of all teams
        if member.get("orgRole") == "owner":
            m["team_ids"] = all_team_ids
            m["admin_team_ids"] = all_team_ids
        else:
            memberships = team_memberships.get(str(member["id"]), [])
            m["team_ids"] = [tid for tid, _ in memberships]
            m["admin_team_ids"] = [tid for tid, role in memberships if role == "admin"]
        result.append(m)
    return result


def load_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
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
