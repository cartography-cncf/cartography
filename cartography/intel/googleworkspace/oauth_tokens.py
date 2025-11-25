import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.oauth_token import (
    GoogleWorkspaceOAuthTokenSchema,
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
    :param user_id: User ID
    :return: list of OAuth tokens for the user
    """
    try:
        request = admin.tokens().list(userKey=user_id)
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        tokens = resp.get("items", [])

        # Add user_key to each token for relationship mapping
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
            logger.debug(f"No OAuth tokens found for user {user_id}")
            return []
        else:
            logger.warning(f"Error fetching OAuth tokens for user {user_id}: {e}")
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
def transform_oauth_tokens(tokens: list[dict]) -> list[dict[str, Any]]:
    """
    Transform OAuth token objects to flatten structure

    :param tokens: Raw API response token objects
    :return: list of dictionary objects for data model consumption
    """
    results = []
    for token in tokens:
        transformed_token = {
            "client_id": token.get("clientId"),
            "display_text": token.get("displayText"),
            "anonymous": token.get("anonymous", False),
            "native_app": token.get("nativeApp", False),
            "user_id": token.get("user_key"),
            "scopes": token.get("scopes", []),
            # Combine clientId and userKey to create a unique ID
            "id": f"{token.get('clientId')}:{token.get('user_key')}",
        }
        results.append(transformed_token)

    return results


@timeit
def load_googleworkspace_oauth_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    googleworkspace_update_tag: int,
    customer_id: str,
) -> None:
    """
    Load Google Workspace OAuth tokens
    """
    logger.info(
        "Ingesting %s Google Workspace OAuth tokens for customer %s",
        len(data),
        customer_id,
    )
    load(
        neo4j_session,
        GoogleWorkspaceOAuthTokenSchema(),
        data,
        lastupdated=googleworkspace_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def cleanup_googleworkspace_oauth_tokens(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up Google Workspace OAuth tokens
    """
    logger.debug("Running Google Workspace OAuth tokens cleanup job")
    GraphJob.from_node_schema(
        GoogleWorkspaceOAuthTokenSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_googleworkspace_oauth_tokens(
    neo4j_session: neo4j.Session,
    admin: Resource,
    user_ids: list[str],
    googleworkspace_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    GET Google Workspace OAuth token objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    :param user_ids: List of user IDs to fetch tokens for
    :param googleworkspace_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing Google Workspace OAuth Tokens")

    # 1. GET - Fetch data from API
    tokens = get_all_oauth_tokens(admin, user_ids)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_tokens = transform_oauth_tokens(tokens)

    # 3. LOAD - Ingest to Neo4j using data model
    load_googleworkspace_oauth_tokens(
        neo4j_session,
        transformed_tokens,
        googleworkspace_update_tag,
        common_job_parameters["CUSTOMER_ID"],
    )

    # 4. CLEANUP - Remove stale data
    cleanup_googleworkspace_oauth_tokens(neo4j_session, common_job_parameters)
