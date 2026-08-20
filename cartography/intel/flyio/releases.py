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
from cartography.models.flyio.release import FlyReleaseSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_RELEASES_QUERY = """
query ($appName: String!, $limit: Int!, $after: String) {
  app(name: $appName) {
    releases(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        version
        stable
        inProgress
        reason
        description
        status
        deploymentStrategy
        evaluationId
        createdAt
        imageRef
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
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get(
        api_session,
        common_job_parameters["GRAPHQL_URL"],
        common_job_parameters["APP_NAME"],
    )
    releases = transform(response)
    load_releases(
        neo4j_session,
        releases,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return releases


@timeit
def get(
    api_session: requests.Session,
    graphql_url: str,
    app_name: str,
    page_size: int = 100,
) -> dict[str, Any]:
    releases: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        response = post_graphql(
            api_session,
            graphql_url,
            FLY_RELEASES_QUERY,
            {"appName": app_name, "limit": page_size, "after": after},
        )
        app = response.get("app") or {}
        release_connection = app.get("releases") or {}
        releases.extend(require_list(release_connection.get("nodes"), "releases.nodes"))
        page_info = release_connection.get("pageInfo") or {}
        next_cursor = get_next_cursor(page_info, after, "releases")
        if not next_cursor:
            break
        after = next_cursor
    return {"app": {"releases": {"nodes": releases}}}


def transform(response: dict[str, Any]) -> list[dict[str, Any]]:
    app = response.get("app") or {}
    releases = app.get("releases") or {}
    result = []
    for release in require_list(releases.get("nodes"), "releases.nodes"):
        release_id = require_non_empty(release.get("id"), "release id")
        result.append({"id": release_id, **_transform_release(release)})
    return result


def _transform_release(release: dict[str, Any]) -> dict[str, Any]:
    user = release.get("user") or {}
    return {
        "version": release.get("version"),
        "stable": release.get("stable"),
        "in_progress": release.get("inProgress"),
        "reason": release.get("reason"),
        "description": release.get("description"),
        "status": release.get("status"),
        "deployment_strategy": release.get("deploymentStrategy"),
        "evaluation_id": release.get("evaluationId"),
        "created_at": release.get("createdAt"),
        "image_ref": release.get("imageRef"),
        "user_id": user.get("id"),
        "user_name": user.get("name"),
        "user_email": user.get("email"),
    }


@timeit
def load_releases(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyReleaseSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyReleaseSchema(), common_job_parameters).run(
        neo4j_session,
    )
