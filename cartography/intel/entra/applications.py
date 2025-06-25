import logging
from typing import Any

import neo4j
from azure.identity import ClientSecretCredential
from msgraph.generated.models.app_role_assignment import AppRoleAssignment
from msgraph.generated.models.application import Application
from msgraph.graph_service_client import GraphServiceClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.application import EntraApplicationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_entra_applications(client: GraphServiceClient) -> list[Application]:
    """Get all applications from Microsoft Graph API with pagination."""
    all_apps: list[Application] = []
    request_configuration = client.applications.ApplicationsRequestBuilderGetRequestConfiguration(
        query_parameters=client.applications.ApplicationsRequestBuilderGetQueryParameters(
            top=999
        )
    )
    page = await client.applications.get(request_configuration=request_configuration)
    while page:
        if page.value:
            all_apps.extend(page.value)
        if not page.odata_next_link:
            break
        page = await client.applications.with_url(page.odata_next_link).get()
    return all_apps


@timeit
async def get_app_role_assignments(
    client: GraphServiceClient,
) -> list[AppRoleAssignment]:
    """Get all app role assignments from Microsoft Graph API with pagination."""
    all_assignments: list[AppRoleAssignment] = []

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
                        all_assignments.extend(user_assignments)
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
                        all_assignments.extend(group_assignments)
                except Exception as e:
                    logger.warning(
                        f"Could not fetch app role assignments for group {group.id}: {e}"
                    )
                    continue

        # Handle pagination for groups
        if not groups_page.odata_next_link:
            break
        groups_page = await client.groups.with_url(groups_page.odata_next_link).get()

    return all_assignments


@timeit
def transform_applications(apps: list[Application]) -> list[dict[str, Any]]:
    """Transform API response into dictionaries for ingestion."""
    result: list[dict[str, Any]] = []
    for app in apps:
        transformed = {
            "id": app.id,
            "app_id": app.app_id,
            "display_name": app.display_name,
            "sign_in_audience": app.sign_in_audience,
            "publisher_domain": getattr(app, "publisher_domain", None),
            "created_date_time": app.created_date_time,
            "deleted_date_time": app.deleted_date_time,
        }
        result.append(transformed)
    return result


@timeit
def transform_app_role_assignments(
    assignments: list[AppRoleAssignment],
) -> list[dict[str, Any]]:
    """Transform app role assignments into dictionaries for ingestion."""
    result: list[dict[str, Any]] = []
    for assignment in assignments:
        transformed = {
            "id": assignment.id,
            "app_role_id": (
                str(assignment.app_role_id) if assignment.app_role_id else None
            ),
            "principal_id": (
                str(assignment.principal_id) if assignment.principal_id else None
            ),  # User ID
            "principal_display_name": assignment.principal_display_name,
            "principal_type": assignment.principal_type,
            "resource_id": (
                str(assignment.resource_id) if assignment.resource_id else None
            ),  # Service Principal ID of the app
            "resource_display_name": assignment.resource_display_name,
            "created_date_time": assignment.created_date_time,
        }
        result.append(transformed)
    return result


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    apps: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    logger.info(f"Loading {len(apps)} Entra applications")
    load(
        neo4j_session,
        EntraApplicationSchema(),
        apps,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_app_role_assignments(
    neo4j_session: neo4j.Session,
    assignments: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """Load app role assignments as relationships between users/groups and applications."""
    logger.info(f"Loading {len(assignments)} app role assignments")

    # Create relationships between users and applications
    user_query = """
    UNWIND $assignments AS assignment
    WITH assignment
    WHERE assignment.principal_type = "User"
    MATCH (user:EntraUser {id: assignment.principal_id})
    MATCH (app:EntraApplication {display_name: assignment.resource_display_name})
    MERGE (user)-[r:HAS_APP_ROLE]->(app)
    SET r.app_role_id = assignment.app_role_id,
        r.assignment_id = assignment.id,
        r.resource_id = assignment.resource_id,
        r.created_date_time = assignment.created_date_time,
        r.lastupdated = $update_tag
    RETURN count(r) as relationships_created
    """

    # Create relationships between groups and applications
    group_query = """
    UNWIND $assignments AS assignment
    WITH assignment
    WHERE assignment.principal_type = "Group"
    MATCH (group:EntraGroup {id: assignment.principal_id})
    MATCH (app:EntraApplication {display_name: assignment.resource_display_name})
    MERGE (group)-[r:HAS_APP_ROLE]->(app)
    SET r.app_role_id = assignment.app_role_id,
        r.assignment_id = assignment.id,
        r.resource_id = assignment.resource_id,
        r.created_date_time = assignment.created_date_time,
        r.lastupdated = $update_tag
    RETURN count(r) as relationships_created
    """

    # Execute both queries
    user_result = neo4j_session.run(
        user_query, assignments=assignments, update_tag=update_tag
    )
    user_summary = user_result.single()
    user_count = user_summary["relationships_created"] if user_summary else 0

    group_result = neo4j_session.run(
        group_query, assignments=assignments, update_tag=update_tag
    )
    group_summary = group_result.single()
    group_count = group_summary["relationships_created"] if group_summary else 0

    total_count = user_count + group_count
    logger.info(
        f"Created {user_count} user-application and {group_count} group-application relationships ({total_count} total)"
    )


@timeit
def cleanup_applications(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EntraApplicationSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_app_role_assignments(neo4j_session: neo4j.Session, update_tag: int) -> None:
    """Clean up old app role assignment relationships."""
    query = """
    MATCH ()-[r:HAS_APP_ROLE]->()
    WHERE r.lastupdated <> $update_tag
    DELETE r
    """
    neo4j_session.run(query, update_tag=update_tag)


@timeit
async def sync_entra_applications(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Entra applications and user-application relationships."""
    credential = ClientSecretCredential(
        tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Get applications
    applications = await get_entra_applications(client)
    transformed_apps = transform_applications(applications)

    # Get app role assignments (user-application relationships)
    app_role_assignments = await get_app_role_assignments(client)
    transformed_assignments = transform_app_role_assignments(app_role_assignments)

    # Load data
    load_tenant(neo4j_session, {"id": tenant_id}, update_tag)
    load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
    load_app_role_assignments(neo4j_session, transformed_assignments, update_tag)

    # Cleanup
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, update_tag)
