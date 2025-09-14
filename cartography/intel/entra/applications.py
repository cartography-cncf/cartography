import gc
import logging
import re
from typing import Any
from typing import AsyncGenerator
from typing import Generator

import httpx
import neo4j
from azure.identity import ClientSecretCredential
from msgraph.generated.models.app_role_assignment_collection_response import (
    AppRoleAssignmentCollectionResponse,
)
from msgraph.generated.models.application import Application
from msgraph.generated.models.service_principal import ServicePrincipal
from msgraph.graph_service_client import GraphServiceClient

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.intel.entra.users import load_tenant
from cartography.models.entra.app_role_assignment import EntraAppRoleAssignmentSchema
from cartography.models.entra.application import EntraApplicationSchema
from cartography.models.entra.entra_user_to_aws_sso import (
    EntraUserToAWSSSOUserMatchLink,
)
from cartography.models.entra.service_principal import EntraServicePrincipalSchema
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
APP_ROLE_ASSIGNMENTS_PAGE_SIZE = 999


@timeit
async def get_entra_applications(
    client: GraphServiceClient,
) -> AsyncGenerator[Application, None]:
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
    client: GraphServiceClient, app: Application
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Gets app role assignments for a single application with safety limits.

    :param client: GraphServiceClient
    :param app: Application object
    :return: Generator of app role assignment data as dicts
    """
    if not app.app_id:
        logger.warning(f"Application {app.id} has no app_id, skipping")
        return

    logger.info(
        f"Fetching role assignments for application: {app.display_name} ({app.app_id})"
    )

    # First, get the service principal for this application
    service_principals_page = await client.service_principals.get(
        request_configuration=client.service_principals.ServicePrincipalsRequestBuilderGetRequestConfiguration(
            query_parameters=client.service_principals.ServicePrincipalsRequestBuilderGetQueryParameters(
                filter=f"appId eq '{app.app_id}'"
            )
        )
    )

    if not service_principals_page or not service_principals_page.value:
        logger.warning(
            f"No service principal found for application {app.app_id} ({app.display_name}). Continuing."
        )
        return

    service_principal: ServicePrincipal = service_principals_page.value[0]

    # Get assignments for this service principal with pagination and limits
    # Use maximum page size (999) to get more data per request
    # Memory is managed through streaming and batching, not page size
    request_config = client.service_principals.by_service_principal_id(
        service_principal.id
    ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetRequestConfiguration(
        query_parameters=client.service_principals.by_service_principal_id(
            service_principal.id
        ).app_role_assigned_to.AppRoleAssignedToRequestBuilderGetQueryParameters(
            top=APP_ROLE_ASSIGNMENTS_PAGE_SIZE  # Maximum allowed by Microsoft Graph API
        )
    )

    assignments_page: AppRoleAssignmentCollectionResponse | None = (
        await client.service_principals.by_service_principal_id(
            service_principal.id
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
                        "application_app_id": app.app_id,
                    }
                else:
                    page_skipped_count += 1

            # Log page results with details about skipped objects
            if page_skipped_count > 0:
                logger.warning(
                    f"Page {page_count} for {app.display_name}: {page_valid_count} valid assignments, "
                    f"{page_skipped_count} skipped objects. Total valid: {assignment_count}"
                )
            else:
                logger.debug(
                    f"Page {page_count} for {app.display_name}: {page_valid_count} assignments. "
                    f"Total: {assignment_count}"
                )

            # Force garbage collection after each page
            gc.collect()

        # Check if we have more pages to fetch
        if not assignments_page.odata_next_link:
            break

        # Clear previous page before fetching next
        assignments_page.value = None

        # Fetch next page
        logger.debug(
            f"Fetching page {page_count + 1} of assignments for {app.display_name}"
        )
        next_page_url = assignments_page.odata_next_link
        assignments_page = await client.service_principals.with_url(next_page_url).get()

    logger.info(
        f"Successfully retrieved {assignment_count} assignments for application {app.display_name} (pages: {page_count})"
    )


def transform_applications(
    applications: list[Application],
) -> Generator[dict[str, Any], None, None]:
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
            "publisher_domain": app.publisher_domain,
            "sign_in_audience": app.sign_in_audience,
        }


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


def transform_service_principals(
    service_principals: list[ServicePrincipal],
) -> list[dict[str, Any]]:
    result = []
    for spn in service_principals:
        aws_identity_center_instance_id = None
        match = re.search(r"d-[a-z0-9]{10}", spn.login_url or "")
        aws_identity_center_instance_id = match.group(0) if match else None
        transformed = {
            "id": spn.id,
            "app_id": spn.app_id,
            "account_enabled": spn.account_enabled,
            # uuid.UUID to string
            "app_owner_organization_id": (
                str(spn.app_owner_organization_id)
                if spn.app_owner_organization_id
                else None
            ),
            "aws_identity_center_instance_id": aws_identity_center_instance_id,
            "display_name": spn.display_name,
            "login_url": spn.login_url,
            "preferred_single_sign_on_mode": spn.preferred_single_sign_on_mode,
            "preferred_token_signing_key_thumbprint": spn.preferred_token_signing_key_thumbprint,
            "reply_urls": spn.reply_urls,
            "service_principal_type": spn.service_principal_type,
            "sign_in_audience": spn.sign_in_audience,
            "tags": spn.tags,
            # uuid.UUID to string
            "token_encryption_key_id": (
                str(spn.token_encryption_key_id)
                if spn.token_encryption_key_id
                else None
            ),
        }
        result.append(transformed)
    return result


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    applications_data: list[dict[str, Any]],
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
def load_service_principals(
    neo4j_session: neo4j.Session,
    service_principal_data: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str,
) -> None:
    load(
        neo4j_session,
        EntraServicePrincipalSchema(),
        service_principal_data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_applications(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
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
def cleanup_service_principals(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Delete Entra service principals from the graph if they were not updated in the last sync.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing UPDATE_TAG and TENANT_ID
    """
    GraphJob.from_node_schema(EntraServicePrincipalSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_entra_user_to_aws_sso_user_matchlinks(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_matchlink(
        EntraUserToAWSSSOUserMatchLink(),
        "EntraTenant",
        common_job_parameters["TENANT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
async def sync_service_principals(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    update_tag: int,
    tenant_id: str,
) -> None:
    # TODO fix this
    # Service principals
    transformed_service_principals = transform_service_principals(
        service_principals_data
    )
    load_service_principals(
        neo4j_session, transformed_service_principals, update_tag, tenant_id
    )


@timeit
def sync_entra_to_aws_identity_center(
    neo4j_session: neo4j.Session, update_tag: int, tenant_id: str
) -> None:
    query = """
    MATCH (:EntraTenant{id: $TENANT_ID})-[:RESOURCE]->(e:EntraUser)
          -[:HAS_APP_ROLE]->(ar:EntraAppRoleAssignment)
          -[:ASSIGNED_TO]->(n:EntraApplication)
          -[:SERVICE_PRINCIPAL]->(spn:EntraServicePrincipal)
          -[:FEDERATES_TO]->(ic:AWSIdentityCenter)
    MATCH (sso:AWSSSOUser{identity_store_id:ic.identity_store_id})
    WHERE e.user_principal_name = sso.user_name
    RETURN e.user_principal_name as entra_user_principal_name, sso.user_name as aws_user_name
    """
    entrauser_to_awssso_users = neo4j_session.execute_read(
        read_list_of_dicts_tx, query, TENANT_ID=tenant_id
    )

    # Load MatchLink relationships from Entra users to AWS SSO users
    load_matchlinks(
        neo4j_session,
        EntraUserToAWSSSOUserMatchLink(),
        entrauser_to_awssso_users,
        lastupdated=update_tag,
        _sub_resource_label="EntraTenant",
        _sub_resource_id=tenant_id,
    )


@timeit
async def sync_entra_applications(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
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

    # Process applications and their assignments in batches
    app_batch_size = 10  # Batch size for applications
    assignment_batch_size = (
        200  # Batch size for assignments (increased since we handle memory better now)
    )

    apps_batch = []
    assignments_batch = []
    total_assignment_count = 0
    total_app_count = 0

    # Stream apps
    async for app in get_entra_applications(client):
        total_app_count += 1
        apps_batch.append(app)

        # Transform and load applications in batches
        if len(apps_batch) >= app_batch_size:
            transformed_apps = list(transform_applications(apps_batch))
            load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
            logger.info(
                f"Loaded batch of {len(apps_batch)} applications (total: {total_app_count})"
            )
            apps_batch.clear()
            transformed_apps.clear()
            gc.collect()  # Force garbage collection

        # Stream app role assignments
        async for assignment in get_app_role_assignments_for_app(client, app):
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

    # Process remaining applications
    if apps_batch:
        transformed_apps = list(transform_applications(apps_batch))
        load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
        apps_batch.clear()
        transformed_apps.clear()

    # Process remaining assignments
    if assignments_batch:
        transformed_assignments = transform_app_role_assignments(assignments_batch)
        load_app_role_assignments(
            neo4j_session, transformed_assignments, update_tag, tenant_id
        )
        assignments_batch.clear()
        transformed_assignments.clear()


    # TODO sync spns
    # TODO sync entra to id center
    # TODO make this work with batches
    # sync_entra_to_aws_identity_center(neo4j_session, update_tag, tenant_id)

    # Final garbage collection
    gc.collect()

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
    cleanup_service_principals(neo4j_session, common_job_parameters)
    cleanup_entra_user_to_aws_sso_user_matchlinks(neo4j_session, common_job_parameters)
