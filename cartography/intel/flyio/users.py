import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_next_cursor
from cartography.intel.flyio.util import post_graphql
from cartography.intel.flyio.util import require_list
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.user import FlyUserSchema
from cartography.models.flyio.user import FlyUserToOrganizationMemberMatchLink
from cartography.models.flyio.user import FlyUserToOrganizationResourceMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_ORG_MEMBERS_QUERY = """
query ($slug: String!, $limit: Int!, $after: String) {
  organization(slug: $slug) {
    members(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        role
        joinedAt
        node {
          id
          name
          email
        }
      }
    }
  }
}
"""


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get(
        api_session,
        common_job_parameters["GRAPHQL_URL"],
        common_job_parameters["ORGANIZATION_ID"],
    )
    users = transform(response)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["UPDATE_TAG"],
    )
    load_user_relationships(
        neo4j_session,
        users,
        common_job_parameters["ORGANIZATION_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return users


@timeit
def get(
    api_session: requests.Session,
    graphql_url: str,
    org_slug: str,
    page_size: int = 100,
) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        response = post_graphql(
            api_session,
            graphql_url,
            FLY_ORG_MEMBERS_QUERY,
            {"slug": org_slug, "limit": page_size, "after": after},
        )
        organization = response.get("organization") or {}
        members = organization.get("members") or {}
        edges.extend(require_list(members.get("edges"), "members.edges"))
        after = get_next_cursor(members.get("pageInfo") or {}, after, "members")
        if not after:
            return {"organization": {"members": {"edges": edges}}}


def transform(response: dict[str, Any]) -> list[dict[str, Any]]:
    organization = response.get("organization") or {}
    members = organization.get("members") or {}
    users_by_id = {}
    for edge in require_list(members.get("edges"), "members.edges"):
        user = edge.get("node") or {}
        user_id = require_non_empty(user.get("id"), "user id")
        users_by_id[user_id] = {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "role": edge.get("role"),
            "joined_at": edge.get("joinedAt"),
        }
    return list(users_by_id.values())


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyUserSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_user_relationships(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_slug: str,
    update_tag: int,
) -> None:
    if not data:
        return
    relationship_data = [
        {
            **user,
            "organization_id": org_slug,
        }
        for user in data
    ]
    for matchlink in (
        FlyUserToOrganizationResourceMatchLink(),
        FlyUserToOrganizationMemberMatchLink(),
    ):
        load_matchlinks(
            neo4j_session,
            matchlink,
            relationship_data,
            lastupdated=update_tag,
            _sub_resource_label="FlyOrganization",
            _sub_resource_id=org_slug,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    org_slug = common_job_parameters["ORGANIZATION_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    for matchlink in (
        FlyUserToOrganizationMemberMatchLink(),
        FlyUserToOrganizationResourceMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink,
            "FlyOrganization",
            org_slug,
            update_tag,
        ).run(neo4j_session)
