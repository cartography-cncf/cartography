import gc
import logging
from typing import Any
from typing import AsyncGenerator
from typing import Generator

import neo4j
from azure.identity import ClientSecretCredential
from msgraph.generated.models.application import Application
from msgraph.graph_service_client import GraphServiceClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
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

    # Step 1: Sync applications
    app_batch_size = 10  # Batch size for applications
    apps_batch = []
    total_app_count = 0

    # Stream and load applications
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

    # Process remaining applications
    if apps_batch:
        transformed_apps = list(transform_applications(apps_batch))
        load_applications(neo4j_session, transformed_apps, update_tag, tenant_id)
        apps_batch.clear()
        transformed_apps.clear()
    cleanup_applications(neo4j_session, common_job_parameters)
    logger.info(f"Completed syncing {total_app_count} applications")
    # Final garbage collection
    gc.collect()
