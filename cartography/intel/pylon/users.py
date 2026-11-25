import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.pylon.util import paginated_get
from cartography.models.pylon.user import PylonUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_users = get(api_session, common_job_parameters["BASE_URL"])
    users = transform(raw_users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/users",
        params={"include_deactivated": "true"},
    )


def transform(raw_users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    users = []
    for user in raw_users:
        # `role_id` is deprecated and returns only one of the user's roles.
        role_ids = user.get("role_ids")
        if role_ids is None:
            role_ids = [role["id"] for role in user.get("roles") or []]
        is_deactivated = user.get("is_deactivated")
        users.append(
            {
                "id": user["id"],
                "name": user.get("name"),
                "email": user.get("email") or None,
                "emails": user.get("emails") or [],
                "is_deactivated": is_deactivated,
                "active": None if is_deactivated is None else not is_deactivated,
                "role_ids": sorted(role_ids),
            },
        )
    return users


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Pylon users for organization %s", len(data), org_id)
    load(
        neo4j_session,
        PylonUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PylonUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
