import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jumpcloud.util import paginated_get
from cartography.models.jumpcloud.application import JumpCloudApplicationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_APPLICATIONS_URL = "https://console.jumpcloud.com/api/v2/saas-management/applications"
_APPLICATION_USERS_URL = "https://console.jumpcloud.com/api/v2/saas-management/applications/{application_id}/accounts"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting JumpCloud applications sync")
    raw_apps = get(session)
    transformed = transform(raw_apps)
    load_applications(neo4j_session, transformed, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed JumpCloud applications sync")


def _extract_user_id(user: Any) -> str | None:
    if isinstance(user, (str, int)):
        return str(user) if user else None
    if not isinstance(user, dict):
        return None
    for key in ("user_id", "id", "_id", "userId"):
        value = user.get(key)
        if value and isinstance(value, (str, int)):
            return str(value)
    nested = user.get("user")
    if isinstance(nested, dict):
        for key in ("id", "_id"):
            value = nested.get(key)
            if value and isinstance(value, (str, int)):
                return str(value)
    return None


def _get_application_users(
    session: requests.Session,
    application_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            session,
            _APPLICATION_USERS_URL.format(application_id=application_id),
            skip_param="offset",
        )
    )


@timeit
def get(session: requests.Session) -> list[dict[str, Any]]:
    applications: list[dict[str, Any]] = []
    for app in paginated_get(session, _APPLICATIONS_URL, skip_param="offset"):
        app_id = str(app["id"])
        app["users"] = _get_application_users(session, app_id)
        applications.append(app)
    logger.debug("Fetched %d applications total", len(applications))
    return applications


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": app["id"],
            "name": app.get("catalog_app_id"),
            "user_ids": list(
                dict.fromkeys(
                    uid for user in app.get("users", []) if (uid := user.get("user_id"))
                )
            ),
        }
        for app in api_result
    ]


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        JumpCloudApplicationSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JumpCloudApplicationSchema(), common_job_parameters).run(
        neo4j_session,
    )
