import logging
from typing import Any, AsyncGenerator, Generator
from typing import Dict
from typing import List

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
APP_ROLE_ASSIGNMENTS_PAGE_SIZE = (
    999  # Currently not used, but reserved for future pagination improvements
)

# Warning thresholds for potential data completeness issues
# Log warnings when individual users/groups have more assignments than this threshold
HIGH_ASSIGNMENT_COUNT_THRESHOLD = 100


@timeit
async def get_entra_applications(client: GraphServiceClient) -> AsyncGenerator[Any, None]:
    """
    Gets Entra applications using the Microsoft Graph API with a generator.

    :param client: GraphServiceClient
    :return: Generator of raw Application objects from Microsoft Graph
    """
    count = 0
    # Get all applications with pagination
    request_configuration = client.applications.ApplicationsRequestBuilderGetRequestConfiguration(
        query_parameters=client.applications.ApplicationsRequestBuilderGetQueryParameters(
            top=APPLICATIONS_PAGE_SIZE
        )
    )
    page = await client.applications.get(request_configuration=request_configuration)

    while page:
        if page.value:
            for app in page.value:
                count += 1
                yield app

        if not page.odata_next_link:
            break
        page = await client.applications.with_url(page.odata_next_link).get()

    logger.info(f"Retrieved {count} Entra applications total")


@timeit
async def get_app_role_assignments(
    client: GraphServiceClient, applications: List[Any]
) -> List[Any]:
    """
    Gets app role assignments efficiently by querying each application's service principal.

    :param client: GraphServiceClient
    :param applications: List of Application objects (from get_entra_applications)
    :return: List of raw app role assignment objects from Microsoft Graph
    """
    assignments = []

    for app in applications:
        if not app.app_id:
            logger.warning(f"Application {app.id} has no app_id, skipping")
            continue

        try:
            # First, get the service principal for this application
            # The service principal represents the app in the directory
            service_principals_page = await client.service_principals.get(
                request_configuration=client.service_principals.ServicePrincipalsRequestBuilderGetRequestConfiguration(
                    query_parameters=client.service_principals.ServicePrincipalsRequestBuilderGetQueryParameters(
                        filter=f"appId eq '{app.app_id}'"
                    )
                )
            )

            if not service_principals_page or not service_principals_page.value:
                logger.debug(
                    f"No service principal found for application {app.app_id} ({app.display_name})"
                )
                continue

            service_principal = service_principals_page.value[0]

            # Ensure service principal has an ID
            if not service_principal.id:
                logger.warning(
                    f"Service principal for application {app.app_id} ({app.display_name}) has no ID, skipping"
                )
                continue

            # Get all assignments for this service principal (users, groups, service principals)
            assignments_page = await client.service_principals.by_service_principal_id(
                service_principal.id
            ).app_role_assigned_to.get()

            app_assignments = []
            while assignments_page:
                if assignments_page.value:
                    # Add application context to each assignment
                    for assignment in assignments_page.value:
                        # Add the application app_id to the assignment for relationship matching
                        assignment.application_app_id = app.app_id
                    app_assignments.extend(assignments_page.value)

                if not assignments_page.odata_next_link:
                    break
                assignments_page = await client.service_principals.with_url(
                    assignments_page.odata_next_link
                ).get()

            # Log warning if a single application has many assignments (potential pagination issues)
            if len(app_assignments) >= HIGH_ASSIGNMENT_COUNT_THRESHOLD:
                logger.warning(
                    f"Application {app.display_name} ({app.app_id}) has {len(app_assignments)} role assignments. "
                    f"If this seems unexpectedly high, there may be pagination limits affecting data completeness."
                )

            assignments.extend(app_assignments)
            logger.debug(
                f"Retrieved {len(app_assignments)} assignments for application {app.display_name}"
            )

        except APIError as e:
            # Handle Microsoft Graph API errors (403 Forbidden, 404 Not Found, etc.)
            if e.response_status_code == 403:
                logger.warning(
                    f"Access denied when fetching app role assignments for application {app.app_id} ({app.display_name}). "
                    f"This application may not have sufficient permissions or may not exist."
                )
            elif e.response_status_code == 404:
                logger.warning(
                    f"Application {app.app_id} ({app.display_name}) not found when fetching app role assignments. "
                    f"Application may have been deleted or does not exist."
                )
            elif e.response_status_code == 429:
                logger.warning(
                    f"Rate limit hit when fetching app role assignments for application {app.app_id} ({app.display_name}). "
                    f"Consider reducing APPLICATIONS_PAGE_SIZE or implementing retry logic."
                )
            else:
                logger.warning(
                    f"Microsoft Graph API error when fetching app role assignments for application {app.app_id} ({app.display_name}): "
                    f"Status {e.response_status_code}, Error: {str(e)}"
                )
            continue
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            # Handle network-related errors
            logger.warning(
                f"Network error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}"
            )
            continue
        except Exception as e:
            # Only catch truly unexpected errors - these should be rare
            logger.error(
                f"Unexpected error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}",
                exc_info=True,
            )
            continue

    logger.info(f"Retrieved {len(assignments)} app role assignments total")
    return assignments


def transform_applications(applications: List[Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Transform application data for graph loading using a generator.

    :param applications: Raw Application objects from Microsoft Graph API
    :return: Generator of transformed application data for graph loading
    """
    for app in applications:
        yield {
            "id": app.id,
            "app_id": app.app_id,
            "display_name": app.display_name,
            "publisher_domain": getattr(app, "publisher_domain", None),
            "sign_in_audience": app.sign_in_audience,
        }


def transform_app_role_assignments(
    assignments: List[Any],
) -> Generator[Dict[str, Any], None, None]:
    """
    Transform app role assignment data for graph loading using a generator.

    :param assignments: Raw app role assignment objects from Microsoft Graph API
    :return: Generator of transformed assignment data for graph loading
    """
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

    # Process applications and their assignments in batches
    batch_size = 50  # Smaller batch for applications as they have associated role assignments
    apps_batch = []
    all_assignments = []
    
    async for app in get_entra_applications(client):
        apps_batch.append(app)
        
        if len(apps_batch) >= batch_size:
            # Get role assignments for this batch
            batch_assignments = await get_app_role_assignments(client, apps_batch)
            all_assignments.extend(batch_assignments)
            
            # Transform and load this batch
            transformed_apps = list(transform_applications(apps_batch))
            load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
            
            apps_batch.clear()
    
    # Process remaining applications
    if apps_batch:
        batch_assignments = await get_app_role_assignments(client, apps_batch)
        all_assignments.extend(batch_assignments)
        
        transformed_apps = list(transform_applications(apps_batch))
        load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
    
    # Load all role assignments (these are already batched by application)
    transformed_assignments = list(transform_app_role_assignments(all_assignments))
    load_app_role_assignments(
        neo4j_session, transformed_assignments, update_tag, tenant_id
    )

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
