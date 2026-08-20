import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_next_cursor
from cartography.intel.flyio.util import post_graphql
from cartography.intel.flyio.util import require_list
from cartography.intel.flyio.util import require_non_empty
from cartography.models.flyio.access_token import FlyAppAccessTokenSchema
from cartography.models.flyio.access_token import FlyOrganizationAccessTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_ORG_ACCESS_TOKENS_QUERY = """
query ($slug: String!, $limit: Int!, $after: String) {
  organization(slug: $slug) {
    limitedAccessTokens(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        name
        expiresAt
        revokedAt
        user {
          id
          name
          email
        }
      }
    }
  }
}
"""

FLY_APP_ACCESS_TOKENS_QUERY = """
query ($appName: String!, $limit: Int!, $after: String) {
  app(name: $appName) {
    limitedAccessTokens(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        name
        expiresAt
        revokedAt
        user {
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
def sync_organization(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get_organization(
        api_session,
        common_job_parameters["GRAPHQL_URL"],
        common_job_parameters["ORGANIZATION_ID"],
    )
    tokens = transform_organization_tokens(response)
    load_organization_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["ORGANIZATION_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_organization_tokens(neo4j_session, common_job_parameters)
    return tokens


@timeit
def sync_app(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get_app(
        api_session,
        common_job_parameters["GRAPHQL_URL"],
        common_job_parameters["APP_NAME"],
    )
    tokens = transform_app_tokens(response)
    load_app_tokens(
        neo4j_session,
        tokens,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_app_tokens(neo4j_session, common_job_parameters)
    return tokens


@timeit
def get_organization(
    api_session: requests.Session,
    graphql_url: str,
    org_slug: str,
    page_size: int = 100,
) -> dict[str, Any]:
    tokens = _get_token_connection(
        api_session,
        graphql_url,
        FLY_ORG_ACCESS_TOKENS_QUERY,
        {"slug": org_slug},
        ("organization", "limitedAccessTokens"),
        page_size,
    )
    return {"organization": {"limitedAccessTokens": {"nodes": tokens}}}


@timeit
def get_app(
    api_session: requests.Session,
    graphql_url: str,
    app_name: str,
    page_size: int = 100,
) -> dict[str, Any]:
    tokens = _get_token_connection(
        api_session,
        graphql_url,
        FLY_APP_ACCESS_TOKENS_QUERY,
        {"appName": app_name},
        ("app", "limitedAccessTokens"),
        page_size,
    )
    return {"app": {"limitedAccessTokens": {"nodes": tokens}}}


def _get_token_connection(
    api_session: requests.Session,
    graphql_url: str,
    query: str,
    base_variables: dict[str, Any],
    connection_path: tuple[str, str],
    page_size: int,
) -> list[dict[str, Any]]:
    tokens: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        response = post_graphql(
            api_session,
            graphql_url,
            query,
            {**base_variables, "limit": page_size, "after": after},
        )
        parent = response.get(connection_path[0]) or {}
        connection = parent.get(connection_path[1]) or {}
        tokens.extend(
            require_list(connection.get("nodes"), f"{connection_path[1]}.nodes")
        )
        after = get_next_cursor(
            connection.get("pageInfo") or {},
            after,
            connection_path[1],
        )
        if not after:
            return tokens


def transform_organization_tokens(response: dict[str, Any]) -> list[dict[str, Any]]:
    organization = response.get("organization") or {}
    tokens = organization.get("limitedAccessTokens") or {}
    return transform(require_list(tokens.get("nodes"), "limitedAccessTokens.nodes"))


def transform_app_tokens(response: dict[str, Any]) -> list[dict[str, Any]]:
    app = response.get("app") or {}
    tokens = app.get("limitedAccessTokens") or {}
    return transform(require_list(tokens.get("nodes"), "limitedAccessTokens.nodes"))


def transform(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for token in tokens:
        token_id = require_non_empty(token.get("id"), "access token id")
        user = token.get("user") or {}
        result.append(
            {
                "id": token_id,
                "name": token.get("name"),
                "expires_at": token.get("expiresAt"),
                "revoked_at": token.get("revokedAt"),
                "user_id": user.get("id"),
                "user_name": user.get("name"),
                "user_email": user.get("email"),
                "revoked": token.get("revokedAt") is not None,
            },
        )
    return result


@timeit
def load_organization_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_slug: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyOrganizationAccessTokenSchema(),
        data,
        lastupdated=update_tag,
        ORGANIZATION_ID=org_slug,
    )


@timeit
def load_app_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyAppAccessTokenSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup_organization_tokens(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        FlyOrganizationAccessTokenSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_app_tokens(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyAppAccessTokenSchema(), common_job_parameters).run(
        neo4j_session,
    )
