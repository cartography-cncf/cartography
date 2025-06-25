import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from azure.identity import ClientSecretCredential
from msgraph.graph_service_client import GraphServiceClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.application import EntraApplicationSchema
from cartography.models.entra.application import EntraAppRoleAssignmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_entra_applications(client: GraphServiceClient) -> List[Dict[str, Any]]:
    """
    Gets Entra applications using the Microsoft Graph API.

    :param client: GraphServiceClient
    :return: List of Entra application data
    """
    applications = []

    # Get all applications with pagination
    request_configuration = client.applications.ApplicationsRequestBuilderGetRequestConfiguration(
        query_parameters=client.applications.ApplicationsRequestBuilderGetQueryParameters(
            top=999
        )
    )
    page = await client.applications.get(request_configuration=request_configuration)

    while page:
        if page.value:
            for app in page.value:
                app_data = {
                    "id": app.id,
                    "app_id": app.app_id,
                    "display_name": app.display_name,
                    "publisher_domain": getattr(app, "publisher_domain", None),
                    "sign_in_audience": app.sign_in_audience,
                }
                applications.append(app_data)

        if not page.odata_next_link:
            break
        page = await client.applications.with_url(page.odata_next_link).get()

    return applications


@timeit
async def get_app_role_assignments(client: GraphServiceClient) -> List[Dict[str, Any]]:
    """
    Gets app role assignments for both users and groups using the Microsoft Graph API.

    :param client: GraphServiceClient
    :return: List of app role assignment data
    """
    assignments = []

    # Get all users and their app role assignments
    users_page = await client.users.get()

    while users_page:
        if users_page.value:
            for user in users_page.value:
                if not user.id:
                    continue
                try:
                    # Get app role assignments for this user
                    assignments_page = await client.users.by_user_id(
                        user.id
                    ).app_role_assignments.get()
                    if assignments_page and assignments_page.value:
                        # Filter for assignments where principalType is User
                        user_assignments = [
                            assignment
                            for assignment in assignments_page.value
                            if assignment.principal_type == "User"
                        ]
                        for assignment in user_assignments:
                            assignment_data = {
                                "id": assignment.id,
                                "app_role_id": (
                                    str(assignment.app_role_id)
                                    if assignment.app_role_id
                                    else None
                                ),
                                "created_date_time": assignment.created_date_time,
                                "principal_display_name": assignment.principal_display_name,
                                "principal_type": assignment.principal_type,
                                "resource_display_name": assignment.resource_display_name,
                            }
                            assignments.append(assignment_data)
                except Exception as e:
                    logger.warning(
                        f"Could not fetch app role assignments for user {user.id}: {e}"
                    )
                    continue

        # Handle pagination for users
        if not users_page.odata_next_link:
            break
        users_page = await client.users.with_url(users_page.odata_next_link).get()

    # Get all groups and their app role assignments
    groups_page = await client.groups.get()

    while groups_page:
        if groups_page.value:
            for group in groups_page.value:
                if not group.id:
                    continue
                try:
                    # Get app role assignments for this group
                    assignments_page = await client.groups.by_group_id(
                        group.id
                    ).app_role_assignments.get()
                    if assignments_page and assignments_page.value:
                        # Filter for assignments where principalType is Group
                        group_assignments = [
                            assignment
                            for assignment in assignments_page.value
                            if assignment.principal_type == "Group"
                        ]
                        for assignment in group_assignments:
                            assignment_data = {
                                "id": assignment.id,
                                "app_role_id": (
                                    str(assignment.app_role_id)
                                    if assignment.app_role_id
                                    else None
                                ),
                                "created_date_time": assignment.created_date_time,
                                "principal_display_name": assignment.principal_display_name,
                                "principal_type": assignment.principal_type,
                                "resource_display_name": assignment.resource_display_name,
                            }
                            assignments.append(assignment_data)
                except Exception as e:
                    logger.warning(
                        f"Could not fetch app role assignments for group {group.id}: {e}"
                    )
                    continue

        # Handle pagination for groups
        if not groups_page.odata_next_link:
            break
        groups_page = await client.groups.with_url(groups_page.odata_next_link).get()

    return assignments


def transform_applications(applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform application data for graph loading.

    :param applications: Raw application data from API
    :return: Transformed application data
    """
    result = []
    for app in applications:
        transformed = {
            "id": app["id"],
            "app_id": app["app_id"],
            "display_name": app["display_name"],
            "publisher_domain": app["publisher_domain"],
            "sign_in_audience": app["sign_in_audience"],
        }
        result.append(transformed)
    return result


def transform_app_role_assignments(
    assignments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform app role assignment data for graph loading.

    :param assignments: Raw assignment data from API
    :return: Transformed assignment data
    """
    result = []
    for assignment in assignments:
        transformed = {
            "id": assignment["id"],
            "app_role_id": assignment["app_role_id"],
            "created_date_time": assignment["created_date_time"],
            "principal_display_name": assignment["principal_display_name"],
            "principal_type": assignment["principal_type"],
            "resource_display_name": assignment["resource_display_name"],
        }
        result.append(transformed)
    return result


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    applications_data: List[Dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    """
    Load Entra applications to the graph.

    :param neo4j_session: Neo4j session
    :param applications_data: Application data to load
    :param update_tag: Update tag for tracking data freshness
    :param tenant_id: Entra tenant ID
    """
    load(
        neo4j_session,
        EntraApplicationSchema(),
        applications_data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_app_role_assignments(
    neo4j_session: neo4j.Session,
    assignments_data: List[Dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    """
    Load Entra app role assignments to the graph.

    :param neo4j_session: Neo4j session
    :param assignments_data: Assignment data to load
    :param update_tag: Update tag for tracking data freshness
    :param tenant_id: Entra tenant ID
    """
    load(
        neo4j_session,
        EntraAppRoleAssignmentSchema(),
        assignments_data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_applications(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Delete Entra applications and their relationships from the graph if they were not updated in the last sync.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing UPDATE_TAG and TENANT_ID
    """
    GraphJob.from_node_schema(EntraApplicationSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_app_role_assignments(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Delete Entra app role assignments and their relationships from the graph if they were not updated in the last sync.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing UPDATE_TAG and TENANT_ID
    """
    GraphJob.from_node_schema(
        EntraAppRoleAssignmentSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
async def sync_entra_applications(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Entra applications and their app role assignments to the graph.

    :param neo4j_session: Neo4j session
    :param tenant_id: Entra tenant ID
    :param client_id: Azure application client ID
    :param client_secret: Azure application client secret
    :param update_tag: Update tag for tracking data freshness
    :param common_job_parameters: Common job parameters containing UPDATE_TAG and TENANT_ID
    """
    # Create credentials and client
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    client = GraphServiceClient(
        credential,
        scopes=["https://graph.microsoft.com/.default"],
    )

    # Load tenant (prerequisite)
    load_tenant(neo4j_session, {"id": tenant_id}, update_tag)

    # Get and transform applications data
    applications_data = await get_entra_applications(client)
    transformed_applications = transform_applications(applications_data)

    # Get and transform app role assignments data
    assignments_data = await get_app_role_assignments(client)
    transformed_assignments = transform_app_role_assignments(assignments_data)

    # Load applications and assignments
    load_applications(neo4j_session, transformed_applications, update_tag, tenant_id)
    load_app_role_assignments(
        neo4j_session, transformed_assignments, update_tag, tenant_id
    )

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
