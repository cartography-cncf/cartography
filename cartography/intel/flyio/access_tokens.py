import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import post_graphql
from cartography.models.flyio.access_token import FlyAppAccessTokenSchema
from cartography.models.flyio.access_token import FlyOrganizationAccessTokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_ORG_ACCESS_TOKENS_QUERY = """
query ($slug: String!) {
  organization(slug: $slug) {
    limitedAccessTokens {
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
query ($appName: String!) {
  app(name: $appName) {
    limitedAccessTokens {
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
) -> dict[str, Any]:
    return post_graphql(
        api_session,
        graphql_url,
        FLY_ORG_ACCESS_TOKENS_QUERY,
        {"slug": org_slug},
    )


@timeit
def get_app(
    api_session: requests.Session,
    graphql_url: str,
    app_name: str,
) -> dict[str, Any]:
    return post_graphql(
        api_session,
        graphql_url,
        FLY_APP_ACCESS_TOKENS_QUERY,
        {"appName": app_name},
    )


def transform_organization_tokens(response: dict[str, Any]) -> list[dict[str, Any]]:
    organization = response.get("organization") or {}
    tokens = organization.get("limitedAccessTokens") or {}
    return transform(tokens.get("nodes") or [])


def transform_app_tokens(response: dict[str, Any]) -> list[dict[str, Any]]:
    app = response.get("app") or {}
    tokens = app.get("limitedAccessTokens") or {}
    return transform(tokens.get("nodes") or [])


def transform(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for token in tokens:
        token_id = token.get("id")
        if not token_id:
            continue
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
