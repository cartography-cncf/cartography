import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.user import VercelUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    users = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    users = transform_users(users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return users


def transform_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Vercel returns `joinedFrom` as a map (e.g. {"origin": "mail", ...});
    # flatten to the origin string so Neo4j can store it as a scalar.
    for user in users:
        joined_from = user.get("joinedFrom")
        if isinstance(joined_from, dict):
            user["joinedFrom"] = joined_from.get("origin")
    return users


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v2/teams/{team_id}/members",
        "members",
        team_id,
    )


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelUserSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
