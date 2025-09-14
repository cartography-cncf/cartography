import logging
import re
from typing import Any
from typing import AsyncGenerator

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.service_principal import ServicePrincipal

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.entra.service_principal import EntraServicePrincipalSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

SERVICE_PRINCIPALS_PAGE_SIZE = 999


@timeit
async def get_entra_service_principals(
    client: GraphServiceClient,
) -> AsyncGenerator[ServicePrincipal, None]:
    """
    Gets Entra service principals using the Microsoft Graph API with a generator.

    :param client: GraphServiceClient
    :return: Generator of raw ServicePrincipal objects from Microsoft Graph
    """
    count = 0
    # Get all service principals with pagination
    request_configuration = client.service_principals.ServicePrincipalsRequestBuilderGetRequestConfiguration(
        query_parameters=client.service_principals.ServicePrincipalsRequestBuilderGetQueryParameters(
            top=SERVICE_PRINCIPALS_PAGE_SIZE
        )
    )
    page = await client.service_principals.get(
        request_configuration=request_configuration
    )

    while page:
        if page.value:
            for spn in page.value:
                count += 1
                yield spn

        if not page.odata_next_link:
            break
        page = await client.service_principals.with_url(page.odata_next_link).get()

    logger.info(f"Retrieved {count} Entra service principals total")


async def get_service_principal_by_app_id(
    client: GraphServiceClient, app_id: str
) -> ServicePrincipal | None:
    """
    Gets a service principal by app_id using the Microsoft Graph API.
    This function is extracted from the original app_role_assignments logic.

    :param client: GraphServiceClient
    :param app_id: Application ID to search for
    :return: ServicePrincipal object or None if not found
    """
    service_principals_page = await client.service_principals.get(
        request_configuration=client.service_principals.ServicePrincipalsRequestBuilderGetRequestConfiguration(
            query_parameters=client.service_principals.ServicePrincipalsRequestBuilderGetQueryParameters(
                filter=f"appId eq '{app_id}'"
            )
        )
    )

    if not service_principals_page or not service_principals_page.value:
        logger.warning(
            f"No service principal found for application {app_id}. Continuing."
        )
        return None

    return service_principals_page.value[0]


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
async def sync_service_principals(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra service principals to the graph.

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
    service_principals_batch = []
    batch_size = 50  # Batch size for service principals
    total_count = 0

    # Stream service principals and process in batches
    async for spn in get_entra_service_principals(client):
        service_principals_batch.append(spn)
        total_count += 1

        # Transform and load service principals in batches
        if len(service_principals_batch) >= batch_size:
            transformed_service_principals = transform_service_principals(
                service_principals_batch
            )
            load_service_principals(
                neo4j_session, transformed_service_principals, update_tag, tenant_id
            )
            logger.info(
                f"Loaded batch of {len(service_principals_batch)} service principals (total: {total_count})"
            )
            service_principals_batch.clear()
            transformed_service_principals.clear()

    # Process remaining service principals
    if service_principals_batch:
        transformed_service_principals = transform_service_principals(
            service_principals_batch
        )
        load_service_principals(
            neo4j_session, transformed_service_principals, update_tag, tenant_id
        )
        service_principals_batch.clear()
        transformed_service_principals.clear()

    logger.info(f"Completed loading {total_count} service principals")
    cleanup_service_principals(neo4j_session, common_job_parameters)
