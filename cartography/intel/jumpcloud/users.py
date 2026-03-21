import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jumpcloud.util import paginated_get
from cartography.models.jumpcloud.user import JumpCloudUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_BASE_URL = "https://console.jumpcloud.com/api/systemusers"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting JumpCloud users sync")
    users = get(session)
    transformed_users = transform(users)
    load_users(neo4j_session, transformed_users, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed JumpCloud users sync")


@timeit
def get(session: requests.Session) -> list[dict[str, Any]]:
    return list(paginated_get(session, _BASE_URL))


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user in api_result:
        mfa = user.get("mfa") or {}
        user["mfa_configured"] = mfa.get("configured")
        user["id"] = user.get("_id")
        result.append(user)
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        JumpCloudUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JumpCloudUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
