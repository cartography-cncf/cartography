import json
import logging
from typing import Any

import googleapiclient.discovery
import neo4j
from google.auth.credentials import Credentials as BaseCredentials
from google.auth.exceptions import RefreshError
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.apps_script import (
    GoogleWorkspaceAppsScriptProjectSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5

APPS_SCRIPT_SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/script.projects.readonly",
    "https://www.googleapis.com/auth/script.deployments.readonly",
]

_ACCESS_ORDER = {
    "MYSELF": 0,
    "DOMAIN": 1,
    "ANYONE": 2,
    "ANYONE_ANONYMOUS": 3,
}

_DRIVE_SCRIPT_QUERY = (
    "mimeType='application/vnd.google-apps.script' and 'me' in owners and trashed=false"
)


class _UnauthorizedClientError(Exception):
    """Internal signal when domain-wide delegation lacks Apps Script scopes."""


class _AppsScriptApiDisabledError(Exception):
    """Internal signal when the Drive or Apps Script API is disabled in the Cloud project."""


# Reasons Google returns when an API is not enabled in the Cloud project.
_SERVICE_DISABLED_REASONS = frozenset({"SERVICE_DISABLED", "accessNotConfigured"})
# Each user must turn on the Apps Script API at script.google.com/home/usersettings.
# Until they do, no script of that user can be read, so this is not a sync error.
_USER_SETTING_DISABLED_MESSAGE = "has not enabled the Apps Script API"


def _http_error_details(e: HttpError) -> tuple[str, set[str]]:
    """Return the error message and reason codes from a Google API error body."""
    try:
        body = json.loads(e.content)
    except (TypeError, ValueError):
        return "", set()
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return "", set()
    message = error.get("message")
    reasons: set[str] = set()
    for item in (error.get("errors") or []) + (error.get("details") or []):
        if isinstance(item, dict) and isinstance(item.get("reason"), str):
            reasons.add(item["reason"])
    return (message if isinstance(message, str) else ""), reasons


def _get_active_users_for_tenant(
    neo4j_session: neo4j.Session,
    customer_id: str,
) -> list[dict[str, str]]:
    query = """
    MATCH (:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.suspended, false) = false
      AND u.id IS NOT NULL
      AND u.primary_email IS NOT NULL
    RETURN u.id AS id, u.primary_email AS primary_email
    ORDER BY u.id
    """
    result = neo4j_session.run(query, CUSTOMER_ID=customer_id)
    return [
        {"id": record["id"], "primary_email": record["primary_email"]}
        for record in result
    ]


def _list_user_script_ids(drive: Resource) -> list[str]:
    script_ids: list[str] = []
    page_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "q": _DRIVE_SCRIPT_QUERY,
            "fields": "nextPageToken, files(id)",
            "pageSize": 1000,
        }
        if page_token is not None:
            kwargs["pageToken"] = page_token
        resp = drive.files().list(**kwargs).execute(num_retries=GOOGLE_API_NUM_RETRIES)
        for file_obj in resp.get("files", []):
            file_id = file_obj.get("id")
            if file_id:
                script_ids.append(file_id)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return script_ids


def _get_project_metadata(script: Resource, script_id: str) -> dict[str, Any]:
    return (
        script.projects()
        .get(scriptId=script_id)
        .execute(num_retries=GOOGLE_API_NUM_RETRIES)
    )


def _list_project_deployments(script: Resource, script_id: str) -> list[dict[str, Any]]:
    deployments: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "scriptId": script_id,
            "pageSize": 50,
        }
        if page_token is not None:
            kwargs["pageToken"] = page_token
        resp = (
            script.projects()
            .deployments()
            .list(**kwargs)
            .execute(num_retries=GOOGLE_API_NUM_RETRIES)
        )
        deployments.extend(resp.get("deployments", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return deployments


@timeit
def get_apps_script_projects(
    creds: ServiceAccountCredentials,
    users: list[dict[str, str]],
) -> tuple[list[tuple[str, dict[str, Any], list[dict[str, Any]]]], list[str]]:
    """
    Fetch standalone Apps Script projects and their deployments for each user.

    Returns (raw_projects, read_user_ids). raw_projects is a list of
    (owner_user_id, project, deployments) tuples. read_user_ids lists the users
    whose Drive listing and every listed project were read; only their stale
    projects may be cleaned up. A project deleted between listing and reading does
    not count against its owner. A user whose Apps Script API user setting is off,
    or any other failed read, leaves that user out so their projects are kept.
    """
    raw_projects: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    read_user_ids: list[str] = []
    any_user_authorized = False
    users_with_api_setting_off = 0

    for user in users:
        user_id = user["id"]
        primary_email = user["primary_email"]
        user_creds = creds.with_scopes(APPS_SCRIPT_SCOPES).with_subject(primary_email)
        drive = googleapiclient.discovery.build(
            "drive",
            "v3",
            credentials=user_creds,
            cache_discovery=False,
        )

        try:
            script_ids = _list_user_script_ids(drive)
        except RefreshError as e:
            if not any_user_authorized and "unauthorized_client" in str(e):
                raise _UnauthorizedClientError from e
            logger.debug(
                "Skipping Apps Script Drive list for user %s due to RefreshError",
                user_id,
            )
            continue
        except HttpError as e:
            _, reasons = _http_error_details(e)
            if reasons & _SERVICE_DISABLED_REASONS:
                raise _AppsScriptApiDisabledError from e
            if e.resp.status in (401, 403, 404):
                logger.debug(
                    "Skipping Apps Script Drive list for user %s: HTTP %s",
                    user_id,
                    e.resp.status,
                )
                continue
            raise
        any_user_authorized = True
        user_fully_read = True

        if not script_ids:
            read_user_ids.append(user_id)
            continue

        script = googleapiclient.discovery.build(
            "script",
            "v1",
            credentials=user_creds,
            cache_discovery=False,
        )

        for script_id in script_ids:
            try:
                project = _get_project_metadata(script, script_id)
                deployments = _list_project_deployments(script, script_id)
            except RefreshError:
                logger.debug(
                    "Skipping Apps Script project %s for user %s due to RefreshError",
                    script_id,
                    user_id,
                )
                user_fully_read = False
                continue
            except HttpError as e:
                message, reasons = _http_error_details(e)
                if reasons & _SERVICE_DISABLED_REASONS:
                    raise _AppsScriptApiDisabledError from e
                if e.resp.status == 403 and _USER_SETTING_DISABLED_MESSAGE in message:
                    logger.debug(
                        "Skipping Apps Script projects of user %s: Apps Script API user setting is off",
                        user_id,
                    )
                    users_with_api_setting_off += 1
                    user_fully_read = False
                    break
                if e.resp.status == 404:
                    logger.debug(
                        "Skipping Apps Script project %s for user %s: not found",
                        script_id,
                        user_id,
                    )
                    continue
                if e.resp.status in (401, 403):
                    logger.debug(
                        "Skipping Apps Script project %s for user %s: HTTP %s",
                        script_id,
                        user_id,
                        e.resp.status,
                    )
                    user_fully_read = False
                    continue
                raise

            raw_projects.append((user_id, project, deployments))

        if user_fully_read:
            read_user_ids.append(user_id)

    if users_with_api_setting_off:
        logger.info(
            "Apps Script projects of %s users were not read because their Apps Script API user setting is off",
            users_with_api_setting_off,
        )
    return raw_projects, read_user_ids


def transform_apps_script_project(
    owner_user_id: str,
    project: dict[str, Any],
    deployments: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Transform a single Apps Script project and its deployments into a node dict.
    Deployment IDs and URLs are intentionally excluded.
    """
    versioned_deployments = [
        d
        for d in deployments
        if (d.get("deploymentConfig") or {}).get("versionNumber") is not None
    ]

    best_webapp_rank: tuple[int, int] | None = None
    webapp_access: str | None = None
    webapp_execute_as: str | None = None

    best_api_rank: int = -1
    api_executable_access: str | None = None

    for deployment in versioned_deployments:
        for entry_point in deployment.get("entryPoints") or []:
            ep_type = entry_point.get("entryPointType")
            if ep_type == "WEB_APP":
                config = (entry_point.get("webApp") or {}).get("entryPointConfig") or {}
                access = config.get("access")
                execute_as = config.get("executeAs")
                if access in _ACCESS_ORDER:
                    rank = (
                        _ACCESS_ORDER[access],
                        1 if execute_as == "USER_DEPLOYING" else 0,
                    )
                    if best_webapp_rank is None or rank > best_webapp_rank:
                        best_webapp_rank = rank
                        webapp_access = access
                        webapp_execute_as = execute_as
            elif ep_type == "EXECUTION_API":
                config = (entry_point.get("executionApi") or {}).get(
                    "entryPointConfig"
                ) or {}
                access = config.get("access")
                if access in _ACCESS_ORDER and _ACCESS_ORDER[access] > best_api_rank:
                    best_api_rank = _ACCESS_ORDER[access]
                    api_executable_access = access

    return {
        "id": project["scriptId"],
        "title": project.get("title"),
        "create_time": project.get("createTime"),
        "update_time": project.get("updateTime"),
        "parent_id": project.get("parentId"),
        "creator_email": (project.get("creator") or {}).get("email"),
        "owner_user_id": owner_user_id,
        "versioned_deployment_count": len(versioned_deployments),
        "webapp_access": webapp_access,
        "webapp_execute_as": webapp_execute_as,
        "is_anonymous_webapp_running_as_deployer": (
            webapp_access == "ANYONE_ANONYMOUS"
            and webapp_execute_as == "USER_DEPLOYING"
        ),
        "api_executable_access": api_executable_access,
    }


@timeit
def transform_apps_script_projects(
    raw_projects: list[tuple[str, dict[str, Any], list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    return [
        transform_apps_script_project(owner_user_id, project, deployments)
        for owner_user_id, project, deployments in raw_projects
    ]


@timeit
def load_apps_script_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    customer_id: str,
) -> None:
    logger.info(
        "Ingesting %s Google Workspace Apps Script projects for customer %s",
        len(data),
        customer_id,
    )
    load(
        neo4j_session,
        GoogleWorkspaceAppsScriptProjectSchema(),
        data,
        lastupdated=update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def cleanup_apps_script_projects(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running Google Workspace Apps Script projects cleanup job")
    GraphJob.from_node_schema(
        GoogleWorkspaceAppsScriptProjectSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_apps_script_projects_of_users(
    neo4j_session: neo4j.Session,
    user_ids: list[str],
    update_tag: int,
    customer_id: str,
) -> None:
    """
    Remove stale projects owned by the given users only.

    Used when some users could not be read: their projects are kept, while users
    whose projects were all read still get deleted scripts removed.
    """
    logger.debug(
        "Running Google Workspace Apps Script projects cleanup for %s users",
        len(user_ids),
    )
    run_write_query(
        neo4j_session,
        """
        MATCH (:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(p:GoogleWorkspaceAppsScriptProject)
        WHERE p.lastupdated <> $UPDATE_TAG
          AND EXISTS {
            MATCH (u:GoogleWorkspaceUser)-[:OWNS]->(p)
            WHERE u.id IN $USER_IDS
          }
        DETACH DELETE p
        """,
        CUSTOMER_ID=customer_id,
        UPDATE_TAG=update_tag,
        USER_IDS=user_ids,
    )
    run_write_query(
        neo4j_session,
        """
        MATCH (:GoogleWorkspaceTenant {id: $CUSTOMER_ID})-[:RESOURCE]->(p:GoogleWorkspaceAppsScriptProject)
        MATCH (u:GoogleWorkspaceUser)-[r:OWNS]->(p)
        WHERE u.id IN $USER_IDS
          AND r.lastupdated <> $UPDATE_TAG
        DELETE r
        """,
        CUSTOMER_ID=customer_id,
        UPDATE_TAG=update_tag,
        USER_IDS=user_ids,
    )


@timeit
def sync_googleworkspace_apps_script(
    neo4j_session: neo4j.Session,
    creds: BaseCredentials,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync standalone Google Apps Script projects for active users of the tenant.
    """
    if not isinstance(creds, ServiceAccountCredentials):
        logger.info(
            "Skipping Apps Script sync - requires service account credentials with domain-wide delegation",
        )
        return

    customer_id = common_job_parameters["CUSTOMER_ID"]
    users = _get_active_users_for_tenant(neo4j_session, customer_id)
    if not users:
        logger.info("No active Google Workspace users found for Apps Script sync")
        return

    try:
        raw_projects, read_user_ids = get_apps_script_projects(creds, users)
    except _UnauthorizedClientError:
        logger.info(
            "Skipping Apps Script sync - domain-wide delegation is missing scopes: %s",
            ", ".join(APPS_SCRIPT_SCOPES),
        )
        return
    except _AppsScriptApiDisabledError:
        logger.warning(
            "Skipping Apps Script sync - the Drive API or Apps Script API is not enabled in the Google Cloud project",
        )
        return
    except HttpError as e:
        # Apps Script is optional; do not fail the Google Workspace sync.
        logger.warning(
            "Skipping Apps Script sync - Google API error HTTP %s",
            e.resp.status,
        )
        return

    transformed = transform_apps_script_projects(raw_projects)
    load_apps_script_projects(neo4j_session, transformed, update_tag, customer_id)

    if len(read_user_ids) == len(users):
        cleanup_apps_script_projects(neo4j_session, common_job_parameters)
        return

    logger.warning(
        "Apps Script projects of %s of %s users could not be read completely; "
        "limiting cleanup to the other users so those projects are kept",
        len(users) - len(read_user_ids),
        len(users),
    )
    if read_user_ids:
        cleanup_apps_script_projects_of_users(
            neo4j_session,
            read_user_ids,
            update_tag,
            customer_id,
        )
