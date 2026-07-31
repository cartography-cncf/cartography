import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import post_graphql
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.user import FlyUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_ORG_MEMBERS_QUERY = """
query ($slug: String!) {
  organization(slug: $slug) {
    members {
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
) -> dict[str, Any]:
    return post_graphql(
        api_session,
        graphql_url,
        FLY_ORG_MEMBERS_QUERY,
        {"slug": org_slug},
    )


def transform(response: dict[str, Any]) -> list[dict[str, Any]]:
    organization = response.get("organization") or {}
    members = organization.get("members") or {}
    users_by_id = {}
    for edge in members.get("edges") or []:
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
    org_slug: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyUserSchema(),
        data,
        lastupdated=update_tag,
        ORGANIZATION_ID=org_slug,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
