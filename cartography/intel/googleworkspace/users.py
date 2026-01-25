import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.googleworkspace.user import GoogleWorkspaceUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_users(admin: Resource) -> list[dict]:
    """
    Return list of Google Users in your organization
    Returns empty list if we are unable to enumerate the users for any reasons
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param admin: apiclient discovery resource object
    :return: list of Google users in domain
    see https://developers.google.com/admin-sdk/directory/v1/guides/manage-users#get_all_domain_users
    """
    request = admin.users().list(
        customer="my_customer",
        maxResults=500,
        orderBy="email",
    )
    response_objects = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        response_objects.append(resp)
        request = admin.users().list_next(request, resp)
    return response_objects


@timeit
def transform_users(response_objects: list[dict]) -> list[dict[str, Any]]:
    """Transform list of API response objects to return list of user objects with flattened structure grouped by customerId
    :param response_objects: Raw API response objects
    :return: list of dictionary objects for data model consumption
    """
    results = []
    for response_object in response_objects:
        for user in response_object["users"]:
            # Flatten the nested name structure
            transformed_user = user.copy()
            if "name" in user and isinstance(user["name"], dict):
                transformed_user["name"] = user["name"].get("fullName")
                transformed_user["family_name"] = user["name"].get("familyName")
                transformed_user["given_name"] = user["name"].get("givenName")
            for org in user.get("organizations", []):
                if org.get("primary"):
                    transformed_user["organization_name"] = org.get("name")
                    transformed_user["organization_title"] = org.get("title")
                    transformed_user["organization_department"] = org.get("department")
            results.append(transformed_user)
    return results


@timeit
def load_googleworkspace_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    googleworkspace_update_tag: int,
    customer_id: str,
) -> None:
    """
    Load Google Workspace users
    """
    logger.info(
        "Ingesting %s Google Workspace users for customer %s", len(data), customer_id
    )
    # Load users with relationship to tenant
    load(
        neo4j_session,
        GoogleWorkspaceUserSchema(),
        data,
        lastupdated=googleworkspace_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def cleanup_googleworkspace_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up Google Workspace users
    """
    logger.debug("Running Google Workspace users cleanup job")
    GraphJob.from_node_schema(GoogleWorkspaceUserSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_googleworkspace_users(
    neo4j_session: neo4j.Session,
    admin: Resource,
    googleworkspace_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """
    GET Google Workspace user objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param googleworkspace_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: List of user IDs
    """
    logger.debug("Syncing Google Workspace Users")

    # 1. GET - Fetch data from API
    resp_objs = get_all_users(admin)

    # 2. TRANSFORM - Shape data for ingestion
    raw_users = transform_users(resp_objs)

    # 3. LOAD - Ingest to Neo4j using data model
    load_googleworkspace_users(
        neo4j_session,
        raw_users,
        googleworkspace_update_tag,
        common_job_parameters["CUSTOMER_ID"],
    )

    # 4. CLEANUP - Remove stale data
    cleanup_googleworkspace_users(neo4j_session, common_job_parameters)

    return [user["id"] for user in raw_users]
