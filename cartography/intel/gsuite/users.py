import logging
from typing import Any, Dict, List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gsuite.tenant import GSuiteTenantSchema
from cartography.models.gsuite.user import GSuiteUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_users(admin: Resource) -> List[Dict]:
    """
    Return list of Google Users in your organization
    Returns empty list if we are unable to enumerate the users for any reasons
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param admin: apiclient discovery resource object
    :return: List of Google users in domain
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
def transform_users(response_objects: List[Dict]) -> List[Dict]:
    """Transform list of API response objects to return list of user objects with flattened structure
    :param response_objects: Raw API response objects
    :return: list of dictionary objects for data model consumption
    """
    users: List[Dict] = []
    for response_object in response_objects:
        for user in response_object["users"]:
            # Flatten the nested name structure
            transformed_user = user.copy()
            if "name" in user and isinstance(user["name"], dict):
                transformed_user["name"] = user["name"].get("fullName")
                transformed_user["family_name"] = user["name"].get("familyName")
                transformed_user["given_name"] = user["name"].get("givenName")
            users.append(transformed_user)
    return users


@timeit
def load_gsuite_users(
    neo4j_session: neo4j.Session,
    users: List[Dict],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Load GSuite users using the modern data model
    """
    logger.info(f"Ingesting {len(users)} gsuite users")

    # Load tenant first if it doesn't exist
    tenant_data = [{"id": customer_id}]
    load(
        neo4j_session,
        GSuiteTenantSchema(),
        tenant_data,
        lastupdated=gsuite_update_tag,
    )

    # Load users with relationship to tenant
    load(
        neo4j_session,
        GSuiteUserSchema(),
        users,
        lastupdated=gsuite_update_tag,
        CUSTOMER_ID=customer_id,
    )


@timeit
def cleanup_gsuite_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Clean up GSuite users using the modern data model
    """
    logger.debug("Running GSuite users cleanup job")
    GraphJob.from_node_schema(GSuiteUserSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_gsuite_users(
    neo4j_session: neo4j.Session,
    admin: Resource,
    gsuite_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    GET GSuite user objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gsuite_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GSuite Users")

    # 1. GET - Fetch data from API
    resp_objs = get_all_users(admin)

    # 2. TRANSFORM - Shape data for ingestion
    users = transform_users(resp_objs)

    # Extract customer_id from the first user for tenant relationship
    customer_id = users[0]["customerId"] if users else "unknown"

    # 3. LOAD - Ingest to Neo4j using data model
    load_gsuite_users(neo4j_session, users, customer_id, gsuite_update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup_params = {**common_job_parameters, "CUSTOMER_ID": customer_id}
    cleanup_gsuite_users(neo4j_session, cleanup_params)
