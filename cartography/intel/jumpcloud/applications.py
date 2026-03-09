import logging
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jumpcloud.util import paginated_get
from cartography.models.jumpcloud.application import JumpCloudApplicationSchema
from cartography.models.jumpcloud.tenant import JumpCloudTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_APPLICATIONS_URL = "https://console.jumpcloud.com/api/v2/saas-management/applications"
_APPLICATION_USERS_URL = (
    "https://console.jumpcloud.com/api/v2/saas-management/applications/{application_id}/accounts"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    auth_headers: dict[str, str],
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting JumpCloud applications sync")
    raw_apps = get(auth_headers)
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
    session: Session,
    headers: dict[str, str],
    application_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            session,
            _APPLICATION_USERS_URL.format(application_id=application_id),
            headers,
            _TIMEOUT,
            skip_param="offset",
        )
    )


@timeit
def get(headers: dict[str, str]) -> list[dict[str, Any]]:
    session = Session()
    applications: list[dict[str, Any]] = []
    for app in paginated_get(session, _APPLICATIONS_URL, headers, _TIMEOUT, skip_param="offset"):
        app_id = str(app.get("id") or app.get("_id") or "")
        app["users"] = _get_application_users(session, headers, app_id) if app_id else []
        applications.append(app)
    logger.info("Fetched %d applications total", len(applications))
    return applications


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _extract_app_name(app: dict[str, Any]) -> str | None:
        for key in ("name", "catalog_app_id"):
            value = app.get(key)
            if isinstance(value, (str, int)) and value:
                return str(value)
        return None

    transformed: list[dict[str, Any]] = []
    for app in api_result:
        app_id = str(app.get("id") or app.get("_id") or "")
        if not app_id:
            continue

        users = app.get("users", [])
        user_ids = [uid for uid in (_extract_user_id(user) for user in users) if uid]
        owner_user_id = app.get("owner_user_id")
        if isinstance(owner_user_id, (str, int)) and owner_user_id:
            user_ids.append(str(owner_user_id))
        user_ids = list(dict.fromkeys(user_ids))

        transformed.append(
            {
                "id": app_id,
                "name": _extract_app_name(app),
                "description": app.get("description"),
                "user_ids": user_ids,
            },
        )
    return transformed


def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        JumpCloudTenantSchema(),
        [{"id": org_id}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        JumpCloudApplicationSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(JumpCloudApplicationSchema(), common_job_parameters).run(
        neo4j_session,
    )
