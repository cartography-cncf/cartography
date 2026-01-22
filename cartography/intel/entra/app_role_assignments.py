import gc
from typing import Any
from typing import AsyncGenerator

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.app_role_assignment_collection_response import (
    AppRoleAssignmentCollectionResponse,
)

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.graph.job import GraphJob
from cartography.intel.entra.applications import APP_ROLE_ASSIGNMENTS_PAGE_SIZE
from cartography.intel.entra.applications import logger
from cartography.models.entra.app_role_assignment import EntraAppRoleAssignmentSchema
from cartography.util import timeit


@timeit
async def get_app_role_assignments_for_app(
    client: GraphServiceClient, neo4j_session: neo4j.Session, app_id: str
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Gets app role assignments for a single application by querying the graph for service principal ID.

    :param client: GraphServiceClient
    :param neo4j_session: Neo4j session for querying service principal
    :param app_id: Application ID
    :return: Generator of app role assignment data as dicts
    """
    logger.info(f"Fetching role assignments for application: {app_id}")

    # Query the graph to get the service principal ID for this application
    query = """
    MATCH (sp:EntraServicePrincipal {app_id: $app_id})
    RETURN sp.id as service_principal_id
    """
    service_principal_id = neo4j_session.execute_read(
        read_single_value_tx, query, app_id=app_id
    )

    if not service_principal_id:
        logger.warning(
            f"No service principal found in graph for application {app_id}. Continuing."
        )
        return

    # Get assignments for this service principal with pagination and limits
    # Use maximum page size (999) to get more data per request
    # Memory is managed through streaming and batching, not page size
    request_config = client.service_principals.by_service_principal_id(
        service_principal_id
    ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetRequestConfiguration(
        query_parameters=client.service_principals.by_service_principal_id(
            service_principal_id
        ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetQueryParameters(
            top=APP_ROLE_ASSIGNMENTS_PAGE_SIZE  # Maximum allowed by Microsoft Graph API
        )
    )

    assignments_page: AppRoleAssignmentCollectionResponse | None = (
        await client.service_principals.by_service_principal_id(
            service_principal_id
        ).app_role_assigned_to.get(request_configuration=request_config)
    )

    assignment_count = 0
    page_count = 0

    while assignments_page:
        page_count += 1

        if assignments_page.value:
            page_valid_count = 0
            page_skipped_count = 0

            # Process assignments and immediately yield to avoid accumulation
            for assignment in assignments_page.value:
                # Only yield if we have valid data since it's possible (but unlikely) for assignment.id to be None
                if assignment.principal_id:
                    assignment_count += 1
                    page_valid_count += 1
                    yield {
                        "id": assignment.id,
                        "app_role_id": assignment.app_role_id,
                        "created_date_time": assignment.created_date_time,
                        "principal_id": assignment.principal_id,
                        "principal_display_name": assignment.principal_display_name,
                        "principal_type": assignment.principal_type,
                        "resource_display_name": assignment.resource_display_name,
                        "resource_id": assignment.resource_id,
                        "application_app_id": app_id,
                    }
                else:
                    page_skipped_count += 1

            # Log page results with details about skipped objects
            if page_skipped_count > 0:
                logger.warning(
                    f"Page {page_count} for {app_id}: {page_valid_count} valid assignments, "
                    f"{page_skipped_count} skipped objects. Total valid: {assignment_count}"
                )
            else:
                logger.debug(
                    f"Page {page_count} for {app_id}: {page_valid_count} assignments. "
                    f"Total: {assignment_count}"
                )

            # Force garbage collection after each page
            gc.collect()

        # Check if we have more pages to fetch
        if not assignments_page.odata_next_link:
            break

        # Clear previous page before fetching next
        assignments_page.value = None

        # Fetch next page using the SAME request builder to preserve response typing
        # Using the root service_principals builder here can return ServicePrincipal objects,
        # which lack AppRoleAssignment fields like principal_id. Stay on the
        # app_role_assigned_to builder to ensure AppRoleAssignmentCollectionResponse typing.
        logger.debug(f"Fetching page {page_count + 1} of assignments for {app_id}")
        next_page_url = assignments_page.odata_next_link
        assignments_page = await (
            client.service_principals.by_service_principal_id(service_principal_id)
            .app_role_assigned_to.with_url(next_page_url)
            .get()
        )

    logger.info(
        f"Successfully retrieved {assignment_count} assignments for application {app_id} (pages: {page_count})"
    )


def transform_app_role_assignments(
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform app role assignment data for graph loading.

    :param assignments: Raw app role assignment data as dicts
    :return: Transformed assignment data for graph loading
    """
    transformed = []
    for assign in assignments:
        transformed.append(
            {
                "id": assign["id"],
                "app_role_id": (
                    str(assign["app_role_id"]) if assign["app_role_id"] else None
                ),
                "created_date_time": assign["created_date_time"],
                "principal_id": (
                    str(assign["principal_id"]) if assign["principal_id"] else None
                ),
                "principal_display_name": assign["principal_display_name"],
                "principal_type": assign["principal_type"],
                "resource_display_name": assign["resource_display_name"],
                "resource_id": (
                    str(assign["resource_id"]) if assign["resource_id"] else None
                ),
                "application_app_id": assign["application_app_id"],
            }
        )
    return transformed


@timeit
def load_app_role_assignments(
    neo4j_session: neo4j.Session,
    assignments_data: list[dict[str, Any]],
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
def cleanup_app_role_assignments(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
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
async def sync_app_role_assignments(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra app role assignments to the graph.

    :param neo4j_session: Neo4j session
    :param tenant_id: Entra tenant ID
    :param client_id: Azure application client ID
    :param client_secret: Azure application client secret
    :param update_tag: Update tag for tracking data freshness
    :param common_job_parameters: Common job parameters for cleanup
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
    assignment_batch_size = 200  # Batch size for assignments
    assignments_batch = []
    total_assignment_count = 0

    # Get app_ids from graph instead of streaming from API again
    query = "MATCH (app:EntraApplication) RETURN app.app_id"
    app_ids = neo4j_session.execute_read(read_list_of_values_tx, query)

    for app_id in app_ids:
        # Stream app role assignments (now using graph query for service principal ID)
        async for assignment in get_app_role_assignments_for_app(
            client, neo4j_session, app_id
        ):
            assignments_batch.append(assignment)
            total_assignment_count += 1

            # Transform and load assignments in batches
            if len(assignments_batch) >= assignment_batch_size:
                transformed_assignments = transform_app_role_assignments(
                    assignments_batch
                )
                load_app_role_assignments(
                    neo4j_session, transformed_assignments, update_tag, tenant_id
                )
                logger.debug(f"Loaded batch of {len(assignments_batch)} assignments")
                assignments_batch.clear()
                transformed_assignments.clear()

                # Force garbage collection after batch load
                gc.collect()

    # Process remaining assignments
    if assignments_batch:
        transformed_assignments = transform_app_role_assignments(assignments_batch)
        load_app_role_assignments(
            neo4j_session, transformed_assignments, update_tag, tenant_id
        )
        assignments_batch.clear()
        transformed_assignments.clear()

    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
    logger.info(f"Completed syncing {total_assignment_count} app role assignments")
    # Final garbage collection
    gc.collect()
