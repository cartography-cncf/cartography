import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.gsuite.group import GSuiteGroupSchema
from cartography.models.gsuite.tenant import GSuiteTenantSchema
from cartography.models.gsuite.user import GSuiteUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_groups(admin: Resource) -> List[Dict]:
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of Google groups in domain
    """
    request = admin.groups().list(
        customer="my_customer",
        maxResults=20,
        orderBy="email",
    )
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = admin.groups().list_next(request, resp)
        except HttpError as e:
            if (
                e.resp.status == 403
                and "Request had insufficient authentication scopes" in str(e)
            ):
                logger.error(
                    "Missing required GSuite scopes. If using the gcloud CLI, ",
                    "run: gcloud auth application-default login --scopes="
                    '"https://www.googleapis.com/auth/admin.directory.user.readonly,'
                    "https://www.googleapis.com/auth/admin.directory.group.readonly,"
                    "https://www.googleapis.com/auth/admin.directory.group.member.readonly,"
                    'https://www.googleapis.com/auth/cloud-platform"',
                )
            raise
    return response_objects


@timeit
def transform_groups(response_objects: List[Dict]) -> List[Dict]:
    """Strips list of API response objects to return list of group objects only

    :param response_objects:
    :return: list of dictionary objects as defined in /docs/root/modules/gsuite/schema.md
    """
    groups: List[Dict] = []
    for response_object in response_objects:
        for group in response_object.get("groups", []):
            groups.append(group)
    return groups


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
def get_all_groups_for_email(admin: Resource, email: str) -> List[Dict]:
    """Fetch all groups of which the given group is a member

    Arguments:
        email: A string representing the email address for the group

    Returns a list of Group models
    Throws GoogleException
    """
    request = admin.groups().list(userKey=email, maxResults=500)
    groups: List[Dict] = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        groups = groups + resp.get("groups", [])
        request = admin.groups().list_next(request, resp)
    return groups


@timeit
def get_members_for_group(admin: Resource, group_email: str) -> List[Dict]:
    """Get all members for a google group

    :param group_email: A string representing the email address for the group

    :return: List of dictionaries representing Users or Groups.
    """
    request = admin.members().list(
        groupKey=group_email,
        maxResults=500,
    )
    members: List[Dict] = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        members = members + resp.get("members", [])
        request = admin.members().list_next(request, resp)

    return members


@timeit
def get_all_users(admin: Resource) -> List[Dict]:
    """
    Return list of Google Users in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param admin: apiclient discovery resource object
    see
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
def load_gsuite_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict],
    customer_id: str,
    gsuite_update_tag: int,
) -> None:
    """
    Load GSuite groups using the modern data model
    """
    logger.info(f"Ingesting {len(groups)} gsuite groups")

    # Load tenant first if it doesn't exist
    tenant_data = [{"id": customer_id}]
    load(
        neo4j_session,
        GSuiteTenantSchema(),
        tenant_data,
        lastupdated=gsuite_update_tag,
    )

    # Load groups with relationship to tenant
    load(
        neo4j_session,
        GSuiteGroupSchema(),
        groups,
        lastupdated=gsuite_update_tag,
        CUSTOMER_ID=customer_id,
    )


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
def load_gsuite_members(
    neo4j_session: neo4j.Session,
    group: Dict,
    members: List[Dict],
    gsuite_update_tag: int,
) -> None:
    ingestion_qry = """
        UNWIND $MemberData as member
        MATCH (user:GSuiteUser {id: member.id}),(group:GSuiteGroup {id: $GroupID })
        MERGE (user)-[r:MEMBER_GSUITE_GROUP]->(group)
        ON CREATE SET
        r.firstseen = $UpdateTag
        SET
        r.lastupdated = $UpdateTag
    """
    run_write_query(
        neo4j_session,
        ingestion_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
    )
    membership_qry = """
        UNWIND $MemberData as member
        MATCH(group_1: GSuiteGroup{id: member.id}), (group_2:GSuiteGroup {id: $GroupID})
        MERGE (group_1)-[r:MEMBER_GSUITE_GROUP]->(group_2)
        ON CREATE SET
        r.firstseen = $UpdateTag
        SET
        r.lastupdated = $UpdateTag
    """
    run_write_query(
        neo4j_session,
        membership_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
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
def cleanup_gsuite_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Clean up GSuite groups using the modern data model
    """
    logger.debug("Running GSuite groups cleanup job")
    GraphJob.from_node_schema(GSuiteGroupSchema(), common_job_parameters).run(
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


@timeit
def sync_gsuite_groups(
    neo4j_session: neo4j.Session,
    admin: Resource,
    gsuite_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    GET GSuite group objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gsuite_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GSuite Groups")

    # 1. GET - Fetch data from API
    resp_objs = get_all_groups(admin)

    # 2. TRANSFORM - Shape data for ingestion
    groups = transform_groups(resp_objs)

    # Extract customer_id - for groups we'll use a default since they don't contain customerId
    # In a real scenario, this would come from the admin API or be passed as a parameter
    customer_id = "my_customer"  # This is what GSuite API uses as identifier

    # 3. LOAD - Ingest to Neo4j using data model
    load_gsuite_groups(neo4j_session, groups, customer_id, gsuite_update_tag)

    # Sync group memberships (this stays as-is for now)
    sync_gsuite_members(groups, neo4j_session, admin, gsuite_update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup_params = {**common_job_parameters, "CUSTOMER_ID": customer_id}
    cleanup_gsuite_groups(neo4j_session, cleanup_params)


@timeit
def sync_gsuite_members(
    groups: List[Dict],
    neo4j_session: neo4j.Session,
    admin: Resource,
    gsuite_update_tag: int,
) -> None:
    for group in groups:
        members = get_members_for_group(admin, group["email"])
        load_gsuite_members(neo4j_session, group, members, gsuite_update_tag)
