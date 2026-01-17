import json
import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.application import WorkOSApplicationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Applications (OAuth and M2M).

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    oauth_apps = get_oauth_applications(client)
    m2m_apps = get_m2m_applications(client)
    transformed_apps = transform(oauth_apps, m2m_apps)
    load_applications(neo4j_session, transformed_apps, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_oauth_applications(client: WorkOSClient) -> list[Any]:
    """
    Fetch OAuth applications from WorkOS API.

    :param client: WorkOS API client
    :return: List of OAuth application objects
    """
    logger.debug("Fetching OAuth applications")
    return paginated_list(client.oauth.list_oauth_applications)


@timeit
def get_m2m_applications(client: WorkOSClient) -> list[Any]:
    """
    Fetch M2M applications from WorkOS API.

    :param client: WorkOS API client
    :return: List of M2M application objects
    """
    logger.debug("Fetching M2M applications")
    return paginated_list(client.m2m.list_m2m_applications)


def transform(oauth_apps: list[Any], m2m_apps: list[Any]) -> list[dict[str, Any]]:
    """
    Transform applications data for loading.

    :param oauth_apps: Raw OAuth application objects from WorkOS
    :param m2m_apps: Raw M2M application objects from WorkOS
    :return: Transformed list of application dicts
    """
    logger.debug(
        f"Transforming {len(oauth_apps)} OAuth and {len(m2m_apps)} M2M WorkOS applications"
    )
    result = []

    # Transform OAuth applications
    for app in oauth_apps:
        app_dict = {
            "id": app.id,
            "client_id": app.client_id,
            "name": app.name,
            "description": getattr(app, "description", None),
            "application_type": "oauth",
            "redirect_uris": (
                json.dumps(app.redirect_uris)
                if hasattr(app, "redirect_uris") and app.redirect_uris
                else None
            ),
            "uses_pkce": getattr(app, "uses_pkce", None),
            "is_first_party": getattr(app, "is_first_party", None),
            "was_dynamically_registered": getattr(
                app, "was_dynamically_registered", None
            ),
            "organization_id": getattr(app, "organization_id", None),
            "scopes": (
                json.dumps(app.scopes)
                if hasattr(app, "scopes") and app.scopes
                else None
            ),
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }
        result.append(app_dict)

    # Transform M2M applications
    for app in m2m_apps:
        app_dict = {
            "id": app.id,
            "client_id": app.client_id,
            "name": app.name,
            "description": getattr(app, "description", None),
            "application_type": "m2m",
            "redirect_uris": None,  # M2M apps don't have redirect_uris
            "uses_pkce": None,  # M2M apps don't have uses_pkce
            "is_first_party": None,  # M2M apps don't have is_first_party
            "was_dynamically_registered": None,  # M2M apps don't have was_dynamically_registered
            "organization_id": app.organization_id,
            "scopes": (
                json.dumps(app.scopes)
                if hasattr(app, "scopes") and app.scopes
                else None
            ),
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }
        result.append(app_dict)

    return result


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load applications into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of application dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS applications into Neo4j")
    load(
        neo4j_session,
        WorkOSApplicationSchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup old applications.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSApplicationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
