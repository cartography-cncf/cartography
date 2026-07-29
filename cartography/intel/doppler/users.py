from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.user import DopplerWorkplaceUserSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(api_session, common_job_parameters["BASE_URL"])
    users = transform(users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/workplace/users", "workplace_users")


def transform(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Flatten the nested `user` object onto the membership record.
    transformed = []
    for member in users:
        user = member.get("user", {}) or {}
        transformed.append(
            {
                "id": member["id"],
                "access": member.get("access"),
                "created_at": member.get("created_at"),
                "email": user.get("email"),
                "name": user.get("name"),
                "username": user.get("username"),
                "profile_image_url": user.get("profile_image_url"),
            }
        )
    return transformed


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerWorkplaceUserSchema(),
        users,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerWorkplaceUserSchema(), common_job_parameters).run(
        neo4j_session
    )
