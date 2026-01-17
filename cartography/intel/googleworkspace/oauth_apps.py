import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.oauth_app import GoogleWorkspaceOAuthAppSchema
from cartography.models.googleworkspace.oauth_app import (
    GoogleWorkspaceUserToOAuthAppRel,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_oauth_tokens_for_user(admin: Resource, user_id: str) -> list[dict]:
    """
    Get OAuth tokens for a specific user
    https://developers.google.com/workspace/admin/directory/reference/rest/v1/tokens/list

    :param admin: apiclient discovery resource object
    :param user_id: User's ID
    :return: list of OAuth tokens for the user
    """
    try:
        request = admin.tokens().list(userKey=user_id)
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        tokens = resp.get("items", [])

        # Add user_id to each token for relationship mapping
        for token in tokens:
            token["user_id"] = user_id

        return tokens
    except HttpError as e:
        if (
            e.resp.status == 403
            and "Request had insufficient authentication scopes" in str(e)
        ):
            logger.error(
                "Missing required Google Workspace scopes. If using the gcloud CLI, "
                "run: gcloud auth application-default login --scopes="
                "https://www.googleapis.com/auth/admin.directory.customer.readonly,"
                "https://www.googleapis.com/auth/admin.directory.user.readonly,"
                "https://www.googleapis.com/auth/admin.directory.user.security,"
                "https://www.googleapis.com/auth/cloud-identity.devices.readonly,"
                "https://www.googleapis.com/auth/cloud-identity.groups.readonly,"
                "https://www.googleapis.com/auth/cloud-platform"
            )
        elif e.resp.status == 404:
            # User has no OAuth tokens, this is normal
            return []
        else:
            logger.warning(f"Error fetching OAuth tokens for user: {e}")
        return []


@timeit
def get_all_oauth_tokens(admin: Resource, user_ids: list[str]) -> list[dict]:
    """
    Get OAuth tokens for all users in the organization

    :param admin: apiclient discovery resource object
    :param user_ids: List of user IDs
    :return: list of all OAuth tokens across all users
    """
    all_tokens = []

    for user_id in user_ids:
        tokens = get_oauth_tokens_for_user(admin, user_id)
        all_tokens.extend(tokens)

    logger.debug(f"Retrieved {len(all_tokens)} OAuth tokens for {len(user_ids)} users")
    return all_tokens


@timeit
def transform_oauth_apps_and_authorizations(
    tokens: list[dict],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Transform OAuth token objects to create app nodes and user authorization relationships

    :param tokens: Raw API response token objects
    :return: tuple of (apps, authorizations)
        - apps: list of unique OAuth app dictionaries
        - authorizations: list of user->app authorization relationships with scopes
    """
    # Group tokens by client_id to create unique apps
    apps_map: dict[str, dict[str, Any]] = {}
    authorizations: list[dict[str, Any]] = []

    for token in tokens:
        client_id = token.get("clientId")
        user_id = token.get("user_id")
        scopes = token.get("scopes", [])

        if not client_id or not user_id:
            logger.warning("Skipping token due to missing client_id or user_id")
            continue

        # Create or update app entry
        if client_id not in apps_map:
            apps_map[client_id] = {
                "client_id": client_id,
                "display_text": token.get("displayText"),
                "anonymous": token.get("anonymous", False),
                "native_app": token.get("nativeApp", False),
            }

        # Create authorization relationship
        authorizations.append(
            {
                "user_id": user_id,
                "client_id": client_id,
                "scopes": scopes,
            }
        )

    apps = list(apps_map.values())
    logger.info(
        f"Transformed {len(apps)} unique OAuth apps with {len(authorizations)} authorizations"
    )
    return apps, authorizations


@timeit
def load_googleworkspace_oauth_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    googleworkspace_update_tag: int,
    customer_id: str,
) -> None:
    """
    Load Google Workspace OAuth apps
    """
    logger.info(
        "Ingesting %s Google Workspace OAuth apps for customer %s",
        len(data),
        customer_id,
    )
    load(
        neo4j_session,
        GoogleWorkspaceOAuthAppSchema(),
        data,
        lastupdated=googleworkspace_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def load_user_to_app_authorizations(
    neo4j_session: neo4j.Session,
    authorizations: list[dict[str, Any]],
    googleworkspace_update_tag: int,
    customer_id: str,
) -> None:
    """
    Load user to OAuth app authorization relationships using MatchLinks
    """
    logger.info(
        "Creating %s user to OAuth app authorization relationships",
        len(authorizations),
    )

    load_matchlinks(
        neo4j_session,
        GoogleWorkspaceUserToOAuthAppRel(),
        authorizations,
        lastupdated=googleworkspace_update_tag,
        _sub_resource_label="GoogleWorkspaceTenant",
        _sub_resource_id=customer_id,
    )


@timeit
def cleanup_googleworkspace_oauth_apps(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up Google Workspace OAuth apps
    """
    logger.debug("Running Google Workspace OAuth apps cleanup job")
    GraphJob.from_node_schema(
        GoogleWorkspaceOAuthAppSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def cleanup_user_to_app_authorizations(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up stale user to OAuth app authorization relationships using MatchLink cleanup
    """
    logger.debug("Running user to OAuth app authorization relationships cleanup")

    GraphJob.from_matchlink(
        GoogleWorkspaceUserToOAuthAppRel(),
        "GoogleWorkspaceTenant",
        common_job_parameters["CUSTOMER_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def sync_googleworkspace_oauth_apps(
    neo4j_session: neo4j.Session,
    admin: Resource,
    user_ids: list[str],
    googleworkspace_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    GET Google Workspace OAuth app objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    :param user_ids: List of user IDs to fetch tokens for
    :param googleworkspace_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing Google Workspace OAuth Apps")

    # 1. GET - Fetch data from API
    tokens = get_all_oauth_tokens(admin, user_ids)

    # 2. TRANSFORM - Shape data for ingestion
    apps, authorizations = transform_oauth_apps_and_authorizations(tokens)

    # 3. LOAD - Ingest apps to Neo4j using data model
    load_googleworkspace_oauth_apps(
        neo4j_session,
        apps,
        googleworkspace_update_tag,
        common_job_parameters["CUSTOMER_ID"],
    )

    # 4. LOAD - Create user to app authorization relationships
    load_user_to_app_authorizations(
        neo4j_session,
        authorizations,
        googleworkspace_update_tag,
        common_job_parameters["CUSTOMER_ID"],
    )

    # 5. CLEANUP - Remove stale data
    cleanup_googleworkspace_oauth_apps(neo4j_session, common_job_parameters)
    cleanup_user_to_app_authorizations(neo4j_session, common_job_parameters)
