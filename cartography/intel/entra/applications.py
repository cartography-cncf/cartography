import gc
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
HIGH_ASSIGNMENT_COUNT_THRESHOLD = 1000

# Maximum number of pages to fetch for app role assignments per application
# Set high to get all data, memory is managed by streaming and batching
MAX_ASSIGNMENT_PAGES_PER_APP = 500

# Maximum assignments to fetch per application
# Set high to get all data, memory is managed by streaming and batching
MAX_ASSIGNMENTS_PER_APP = 100000


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
async def get_app_role_assignments_for_app(
    client: GraphServiceClient, app: Any
) -> AsyncGenerator[Any, None]:
    """
    Gets app role assignments for a single application with safety limits.

    :param client: GraphServiceClient
    :param app: Application object
    :return: Generator of raw app role assignment objects
    """
    if not app.app_id:
        logger.warning(f"Application {app.id} has no app_id, skipping")
        return

    logger.info(f"Fetching role assignments for application: {app.display_name} ({app.app_id})")

    try:
        # First, get the service principal for this application
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
            return

        service_principal = service_principals_page.value[0]

        if not service_principal.id:
            logger.warning(
                f"Service principal for application {app.app_id} ({app.display_name}) has no ID, skipping"
            )
            return

        # Get assignments for this service principal with pagination and limits
        logger.debug(f"Fetching assignments for service principal {service_principal.id}")
        
        # Use smaller page size to reduce memory usage
        request_config = client.service_principals.by_service_principal_id(
            service_principal.id
        ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetRequestConfiguration(
            query_parameters=client.service_principals.by_service_principal_id(
                service_principal.id
            ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetQueryParameters(
                top=100  # Smaller page size to reduce memory
            )
        )
        
        assignments_page = await client.service_principals.by_service_principal_id(
            service_principal.id
        ).app_role_assigned_to.get(request_configuration=request_config)
        
        assignment_count = 0
        page_count = 0
        
        while assignments_page:
            page_count += 1
            
            # Safety check: limit number of pages
            if page_count > MAX_ASSIGNMENT_PAGES_PER_APP:
                logger.warning(
                    f"Reached maximum page limit ({MAX_ASSIGNMENT_PAGES_PER_APP}) for application {app.display_name} ({app.app_id}). "
                    f"Stopping pagination to prevent infinite loop. {assignment_count} assignments fetched so far."
                )
                break
            
            if assignments_page.value:
                # Process assignments and immediately yield to avoid accumulation
                for i, assignment in enumerate(assignments_page.value):
                    # Skip if this is not an app role assignment (might be a ServicePrincipal object)
                    if not hasattr(assignment, 'principal_id'):
                        logger.debug(f"Skipping non-assignment object of type {type(assignment).__name__}")
                        continue
                        
                    # Safety check: limit total assignments
                    if assignment_count >= MAX_ASSIGNMENTS_PER_APP:
                        logger.warning(
                            f"Reached maximum assignment limit ({MAX_ASSIGNMENTS_PER_APP}) for application {app.display_name} ({app.app_id}). "
                            f"Stopping to prevent memory issues."
                        )
                        # Clear references before returning
                        assignments_page = None
                        gc.collect()
                        return
                    
                    # Create minimal assignment dict to reduce memory
                    # Use getattr with defaults to handle missing attributes
                    minimal_assignment = type('MinimalAssignment', (), {
                        'id': getattr(assignment, 'id', None),
                        'app_role_id': getattr(assignment, 'app_role_id', None),
                        'created_date_time': getattr(assignment, 'created_date_time', None),
                        'principal_id': getattr(assignment, 'principal_id', None),
                        'principal_display_name': getattr(assignment, 'principal_display_name', None),
                        'principal_type': getattr(assignment, 'principal_type', None),
                        'resource_display_name': getattr(assignment, 'resource_display_name', None),
                        'resource_id': getattr(assignment, 'resource_id', None),
                        'application_app_id': app.app_id
                    })()
                    
                    # Only yield if we have valid data
                    if minimal_assignment.principal_id:
                        assignment_count += 1
                        yield minimal_assignment
                    
                    # Clear the original assignment to free memory
                    assignments_page.value[i] = None
                
                logger.debug(f"Processed page {page_count} with {assignment_count} assignments so far for {app.display_name}")
                
                # Force garbage collection after each page
                gc.collect()

            if not assignments_page.odata_next_link:
                break
            
            # Clear previous page before fetching next
            assignments_page.value = None
            
            # Fetch next page with error handling
            try:
                logger.debug(f"Fetching page {page_count + 1} of assignments for {app.display_name}")
                assignments_page = await client.service_principals.with_url(
                    assignments_page.odata_next_link
                ).get()
            except Exception as e:
                logger.error(
                    f"Error fetching page {page_count + 1} of assignments for {app.display_name}: {e}. "
                    f"Stopping pagination for this app."
                )
                break

        # Log warning if many assignments
        if assignment_count >= HIGH_ASSIGNMENT_COUNT_THRESHOLD:
            logger.warning(
                f"Application {app.display_name} ({app.app_id}) has {assignment_count} role assignments. "
                f"If this seems unexpectedly high, there may be pagination limits affecting data completeness."
            )
        
        logger.info(
            f"Successfully retrieved {assignment_count} assignments for application {app.display_name} (pages: {page_count})"
        )

    except APIError as e:
        # Handle Microsoft Graph API errors
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
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        logger.warning(
            f"Network error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error when fetching app role assignments for application {app.app_id} ({app.display_name}): {e}",
            exc_info=True,
        )


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

    # Process applications and their assignments in smaller batches
    app_batch_size = 10  # Reduced batch size for applications
    assignment_batch_size = 100  # Reduced batch size for assignments
    
    apps_batch = []
    assignments_batch = []
    total_assignment_count = 0
    total_app_count = 0
    
    async for app in get_entra_applications(client):
        total_app_count += 1
        apps_batch.append(app)
        
        try:
            # Process and stream assignments for each app immediately
            app_assignment_count = 0
            async for assignment in get_app_role_assignments_for_app(client, app):
                # Convert to dict immediately to free SDK object
                assignment_dict = {
                    'id': getattr(assignment, 'id', None),
                    'app_role_id': getattr(assignment, 'app_role_id', None),
                    'created_date_time': getattr(assignment, 'created_date_time', None),
                    'principal_id': getattr(assignment, 'principal_id', None),
                    'principal_display_name': getattr(assignment, 'principal_display_name', None),
                    'principal_type': getattr(assignment, 'principal_type', None),
                    'resource_display_name': getattr(assignment, 'resource_display_name', None),
                    'resource_id': getattr(assignment, 'resource_id', None),
                    'application_app_id': getattr(assignment, 'application_app_id', None)
                }
                assignments_batch.append(assignment_dict)
                total_assignment_count += 1
                app_assignment_count += 1
                
                # Load assignments in batches
                if len(assignments_batch) >= assignment_batch_size:
                    # Transform using dict directly
                    transformed_assignments = []
                    for assign in assignments_batch:
                        transformed_assignments.append({
                            "id": assign['id'],
                            "app_role_id": str(assign['app_role_id']) if assign['app_role_id'] else None,
                            "created_date_time": assign['created_date_time'],
                            "principal_id": str(assign['principal_id']) if assign['principal_id'] else None,
                            "principal_display_name": assign['principal_display_name'],
                            "principal_type": assign['principal_type'],
                            "resource_display_name": assign['resource_display_name'],
                            "resource_id": str(assign['resource_id']) if assign['resource_id'] else None,
                            "application_app_id": assign['application_app_id'],
                        })
                    
                    load_app_role_assignments(
                        neo4j_session, transformed_assignments, update_tag, tenant_id
                    )
                    logger.debug(f"Loaded batch of {len(assignments_batch)} assignments")
                    assignments_batch.clear()
                    transformed_assignments.clear()
                    
                    # Force garbage collection after batch load
                    gc.collect()
            
            if app_assignment_count > 0:
                logger.debug(f"Processed {app_assignment_count} assignments for {app.display_name}")
            
        except Exception as e:
            logger.error(
                f"Error processing assignments for application {app.display_name} ({app.app_id}): {e}. "
                f"Continuing with next application."
            )
            continue
        
        # Load applications in batches and clear memory
        if len(apps_batch) >= app_batch_size:
            transformed_apps = list(transform_applications(apps_batch))
            load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
            logger.info(f"Loaded batch of {len(apps_batch)} applications (total: {total_app_count})")
            apps_batch.clear()
            transformed_apps.clear()
            gc.collect()  # Force garbage collection
    
    # Process remaining applications
    if apps_batch:
        transformed_apps = list(transform_applications(apps_batch))
        load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
        apps_batch.clear()
        transformed_apps.clear()
    
    # Process remaining assignments  
    if assignments_batch:
        # Transform using dict directly
        transformed_assignments = []
        for assign in assignments_batch:
            transformed_assignments.append({
                "id": assign['id'],
                "app_role_id": str(assign['app_role_id']) if assign['app_role_id'] else None,
                "created_date_time": assign['created_date_time'],
                "principal_id": str(assign['principal_id']) if assign['principal_id'] else None,
                "principal_display_name": assign['principal_display_name'],
                "principal_type": assign['principal_type'],
                "resource_display_name": assign['resource_display_name'],
                "resource_id": str(assign['resource_id']) if assign['resource_id'] else None,
                "application_app_id": assign['application_app_id'],
            })
        
        load_app_role_assignments(
            neo4j_session, transformed_assignments, update_tag, tenant_id
        )
        assignments_batch.clear()
        transformed_assignments.clear()
    
    # Final garbage collection
    gc.collect()
    
    logger.info(f"Loaded {total_assignment_count} app role assignments total")

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
