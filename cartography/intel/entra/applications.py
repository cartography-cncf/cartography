import logging
from typing import Any, AsyncIterator, Dict, Iterable, Iterator, List

import httpx
import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError
from msgraph.graph_service_client import GraphServiceClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.app_role_assignment import EntraAppRoleAssignmentSchema
from cartography.models.entra.application import EntraApplicationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Configurable constants for API pagination
# Microsoft Graph API recommends page sizes up to 999 for most resources
# Set to 999 by default, but can be adjusted if needed
#
# Adjust these values if:
# - You have performance issues (decrease values)
# - You want to minimize API calls (increase values up to 999)
# - You're hitting rate limits (decrease values)
APPLICATIONS_PAGE_SIZE = 999
# Flush transformed assignments to Neo4j once this buffer size is reached.
# Keep this comfortably below tx.py's internal 10k batching to limit memory.
ASSIGNMENT_BUFFER_SIZE = 10000  # Align with tx.py 10k batching to reduce DB transactions

# Warning thresholds for potential data completeness issues
# Log warnings when individual users/groups have more assignments than this threshold
HIGH_ASSIGNMENT_COUNT_THRESHOLD = 100


@timeit
async def get_entra_applications(client: GraphServiceClient) -> AsyncIterator[List[Any]]:
    """Yield pages of Entra applications using the Microsoft Graph API."""

    request_configuration = client.applications.ApplicationsRequestBuilderGetRequestConfiguration(
        query_parameters=client.applications.ApplicationsRequestBuilderGetQueryParameters(
            top=APPLICATIONS_PAGE_SIZE,
            select=[
                "id",
                "appId",
                "displayName",
                "signInAudience",
                "publisherDomain",
            ],
        ),
    )
    page = await client.applications.get(request_configuration=request_configuration)

    while page:
        if page.value:
            yield page.value
        if not page.odata_next_link:
            break
        page = await client.applications.with_url(page.odata_next_link).get()


@timeit
async def get_app_role_assignments(
    client: GraphServiceClient, app: Any
) -> List[Any]:
    """Get app role assignments for a single application."""

    if not app.app_id:
        logger.warning(f"Application {app.id} has no app_id, skipping")
        return []

    try:
        service_principals_page = await client.service_principals.get(
            request_configuration=client.service_principals.ServicePrincipalsRequestBuilderGetRequestConfiguration(
                query_parameters=client.service_principals.ServicePrincipalsRequestBuilderGetQueryParameters(
                    filter=f"appId eq '{app.app_id}'",
                    select=["id"],
                ),
            ),
        )

        if not service_principals_page or not service_principals_page.value:
            logger.debug(
                f"No service principal found for application {app.app_id} ({app.display_name})",
            )
            return []

        service_principal = service_principals_page.value[0]

        if not service_principal.id:
            logger.warning(
                f"Service principal for application {app.app_id} ({app.display_name}) has no ID, skipping",
            )
            return []

        assignments_page = await client.service_principals.by_service_principal_id(
            service_principal.id
        ).app_role_assigned_to.get(
            request_configuration=client.service_principals.by_service_principal_id(
                service_principal.id,
            ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetRequestConfiguration(
                query_parameters=client.service_principals.by_service_principal_id(
                    service_principal.id,
                ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetQueryParameters(
                    select=[
                        "id",
                        "appRoleId",
                        "createdDateTime",
                        "principalId",
                        "principalDisplayName",
                        "principalType",
                        "resourceDisplayName",
                        "resourceId",
                    ],
                ),
            ),
        )

        app_assignments: List[Any] = []
        while assignments_page:
            if assignments_page.value:
                for assignment in assignments_page.value:
                    assignment.application_app_id = app.app_id
                app_assignments.extend(assignments_page.value)

            if not assignments_page.odata_next_link:
                break
            assignments_page = await client.service_principals.with_url(
                assignments_page.odata_next_link
            ).get()

        if len(app_assignments) >= HIGH_ASSIGNMENT_COUNT_THRESHOLD:
            logger.warning(
                f"Application {app.display_name} ({app.app_id}) has {len(app_assignments)} role assignments. "
                f"If this seems unexpectedly high, there may be pagination limits affecting data completeness.",
            )

        logger.debug(
            f"Retrieved {len(app_assignments)} assignments for application {app.display_name}",
        )
        return app_assignments

    except APIError as e:
        if e.response_status_code == 403:
            logger.warning(
                f"Access denied when fetching app role assignments for application {app.app_id} ({app.display_name}). "
                f"This application may not have sufficient permissions or may not exist.",
            )
        elif e.response_status_code == 404:
            logger.warning(
                f"Application {app.app_id} ({app.display_name}) not found when fetching app role assignments. "
                f"Application may have been deleted or does not exist.",
            )
        elif e.response_status_code == 429:
            logger.warning(
                f"Rate limit hit when fetching app role assignments for application {app.app_id} ({app.display_name}). "
                f"Consider reducing APPLICATIONS_PAGE_SIZE or implementing retry logic.",
            )
        else:
            logger.warning(
                f"Microsoft Graph API error when fetching app role assignments for application {app.app_id} ({app.display_name}): "
                f"Status {e.response_status_code}, Error: {str(e)}",
            )
        return []
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        logger.warning(
            f"Network error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}",
        )
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}",
            exc_info=True,
        )
        return []


def transform_applications(applications: Iterable[Any]) -> Iterator[Dict[str, Any]]:
    """Transform application data for graph loading."""
    for app in applications:
        yield {
            "id": app.id,
            "app_id": app.app_id,
            "display_name": app.display_name,
            "publisher_domain": getattr(app, "publisher_domain", None),
            "sign_in_audience": app.sign_in_audience,
        }


def transform_app_role_assignments(
    assignments: Iterable[Any],
) -> Iterator[Dict[str, Any]]:
    """Transform app role assignment data for graph loading."""
    for assignment in assignments:
        yield {
            "id": assignment.id,
            "app_role_id": (
                str(assignment.app_role_id) if assignment.app_role_id else None
            ),
            "created_date_time": assignment.created_date_time,
            "principal_id": (
                str(assignment.principal_id) if assignment.principal_id else None
            ),
            "principal_display_name": assignment.principal_display_name,
            "principal_type": assignment.principal_type,
            "resource_display_name": assignment.resource_display_name,
            "resource_id": (
                str(assignment.resource_id) if assignment.resource_id else None
            ),
            "application_app_id": getattr(assignment, "application_app_id", None),
        }


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    applications_data: Iterable[Dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> int:
    """Load Entra applications to the graph."""
    apps_list = applications_data if isinstance(applications_data, list) else list(applications_data)
    load(
        neo4j_session,
        EntraApplicationSchema(),
        apps_list,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )
    return len(apps_list)


@timeit
def load_app_role_assignments(
    neo4j_session: neo4j.Session,
    assignments_data: Iterable[Dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> int:
    """Load Entra app role assignments to the graph."""
    assignments_list = assignments_data if isinstance(assignments_data, list) else list(assignments_data)
    load(
        neo4j_session,
        EntraAppRoleAssignmentSchema(),
        assignments_list,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )
    return len(assignments_list)


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

    total_apps = 0
    total_assignments = 0
    # Buffer for transformed assignments to avoid holding very large lists
    assignments_buffer: List[Dict[str, Any]] = []
    async for apps_page in get_entra_applications(client):
        total_apps += load_applications(
            neo4j_session,
            transform_applications(apps_page),
            update_tag,
            tenant_id,
        )

        # For memory safety, fetch -> transform -> buffer -> flush in chunks per app
        for app in apps_page:
            raw_assignments = await get_app_role_assignments(client, app)
            if not raw_assignments:
                continue
            for ta in transform_app_role_assignments(raw_assignments):
                assignments_buffer.append(ta)
                if len(assignments_buffer) >= ASSIGNMENT_BUFFER_SIZE:
                    total_assignments += load_app_role_assignments(
                        neo4j_session, assignments_buffer, update_tag, tenant_id
                    )
                    assignments_buffer.clear()

    # Flush any remaining assignment records
    if assignments_buffer:
        total_assignments += load_app_role_assignments(
            neo4j_session, assignments_buffer, update_tag, tenant_id
        )
        assignments_buffer.clear()

    logger.info(
        f"Loaded {total_apps} Entra applications and {total_assignments} role assignments"
    )

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
