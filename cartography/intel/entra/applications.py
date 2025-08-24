import logging
import re
from typing import Any

import httpx
import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.app_role_assignment import AppRoleAssignment
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
APP_ROLE_ASSIGNMENTS_PAGE_SIZE = (
    999  # Currently not used, but reserved for future pagination improvements
)

# Warning thresholds for potential data completeness issues
# Log warnings when individual users/groups have more assignments than this threshold
HIGH_ASSIGNMENT_COUNT_THRESHOLD = 100


@timeit
async def get_entra_applications(client: GraphServiceClient) -> list[Application]:
    """
    Gets Entra applications using the Microsoft Graph API.

    :param client: GraphServiceClient
    :return: List of raw Application objects from Microsoft Graph
    """
    applications = []

    # Get all applications with pagination
    request_configuration = client.applications.ApplicationsRequestBuilderGetRequestConfiguration(
        query_parameters=client.applications.ApplicationsRequestBuilderGetQueryParameters(
            top=APPLICATIONS_PAGE_SIZE
        )
    )
    page = await client.applications.get(request_configuration=request_configuration)

    while page:
        if page.value:
            applications.extend(page.value)

        if not page.odata_next_link:
            break
        page = await client.applications.with_url(page.odata_next_link).get()

    logger.info(f"Retrieved {len(applications)} Entra applications total")
    return applications


@timeit
async def get_app_role_assignments(
    client: GraphServiceClient, applications: list[Application]
) -> tuple[list[AppRoleAssignment], list[ServicePrincipal]]:
    """
    Gets app role assignments efficiently by querying each application's service principal.

    :param client: GraphServiceClient
    :param applications: List of Application objects (from get_entra_applications)
    :return: List of raw app role assignment objects from Microsoft Graph
    """
    assignments: list[AppRoleAssignment] = []
    service_principals: list[ServicePrincipal] = []

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
            service_principals.append(service_principal)

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
            raise

    logger.info(f"Retrieved {len(assignments)} app role assignments total")
    return assignments, service_principals


def transform_applications(applications: list[Application]) -> list[dict[str, Any]]:
    """
    Transform application data for graph loading.

    :param applications: Raw Application objects from Microsoft Graph API
    :return: Transformed application data for graph loading
    """
    result = []
    for app in applications:
        transformed = {
            "id": app.id,
            "app_id": app.app_id,
            "display_name": app.display_name,
            "publisher_domain": getattr(app, "publisher_domain", None),
            "sign_in_audience": app.sign_in_audience,
        }
        result.append(transformed)
    return result


def transform_app_role_assignments(
    assignments: list[AppRoleAssignment],
) -> list[dict[str, Any]]:
    """
    Transform app role assignment data for graph loading.

    :param assignments: Raw app role assignment objects from Microsoft Graph API
    :return: Transformed assignment data for graph loading
    """
    result = []
    for assignment in assignments:
        transformed = {
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
        result.append(transformed)
    return result


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
async def sync_entra_apps_roles_spns(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    update_tag: int,
    tenant_id: str,
) -> None:
    # Applications
    applications_data = await get_entra_applications(client)
    transformed_applications = transform_applications(applications_data)
    load_applications(neo4j_session, transformed_applications, update_tag, tenant_id)

    # App roles
    assignments_data, service_principals_data = await get_app_role_assignments(
        client, applications_data
    )
    transformed_assignments = transform_app_role_assignments(assignments_data)
    load_app_role_assignments(
        neo4j_session, transformed_assignments, update_tag, tenant_id
    )

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

    # Load tenant (prerequisite)
    load_tenant(neo4j_session, {"id": tenant_id}, update_tag)

    # Applications, app roles, and service principals
    await sync_entra_apps_roles_spns(neo4j_session, client, update_tag, tenant_id)

    # Attach sign-on relationships
    sync_entra_to_aws_identity_center(neo4j_session, update_tag, tenant_id)

    # Cleanup stale data
    cleanup_applications(neo4j_session, common_job_parameters)
    cleanup_app_role_assignments(neo4j_session, common_job_parameters)
    cleanup_service_principals(neo4j_session, common_job_parameters)
    cleanup_entra_user_to_aws_sso_user_matchlinks(neo4j_session, common_job_parameters)
