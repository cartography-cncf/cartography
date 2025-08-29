# cartography/intel/entra/ou.py
import logging
from typing import Any
from typing import AsyncGenerator
from typing import Generator

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.administrative_unit import AdministrativeUnit

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.entra.ou import EntraOUSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_entra_ous(
    client: GraphServiceClient,
) -> AsyncGenerator[AdministrativeUnit, None]:
    """
    Get all OUs from Microsoft Graph API with pagination support using a generator
    """
    # Initialize first page request
    current_request = client.directory.administrative_units

    while current_request:
        try:
            response = await current_request.get()
            if response and response.value:
                for unit in response.value:
                    yield unit

                # Handle next page using OData link
                if response.odata_next_link:
                    current_request = client.directory.administrative_units.with_url(
                        response.odata_next_link
                    )
                else:
                    current_request = None
            else:
                current_request = None
        except Exception as e:
            logger.error(f"Failed to retrieve administrative units: {str(e)}")
            current_request = None


def transform_ous(
    units: list[AdministrativeUnit], tenant_id: str
) -> Generator[dict[str, Any], None, None]:
    """
    Transform the API response into the format expected by our schema using a generator
    """
    for unit in units:
        yield {
            "id": unit.id,
            "display_name": unit.display_name,
            "description": unit.description,
            "visibility": unit.visibility,
            "membership_type": unit.membership_type,
            "is_member_management_restricted": unit.is_member_management_restricted,
            "deleted_date_time": unit.deleted_date_time,
            "tenant_id": tenant_id,
        }


@timeit
def load_ous(
    neo4j_session: neo4j.Session,
    units: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(f"Loading {len(units)} Entra OUs")
    load(
        neo4j_session,
        EntraOUSchema(),
        units,
        lastupdated=update_tag,
        TENANT_ID=common_job_parameters["TENANT_ID"],
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
    )


def cleanup_ous(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EntraOUSchema(), common_job_parameters).run(neo4j_session)


@timeit
async def sync_entra_ous(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra OUs
    """
    # Initialize Graph client
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Process OUs in batches
    batch_size = 100  # OUs are typically fewer than users/groups
    units_batch = []

    async for unit in get_entra_ous(client):
        units_batch.append(unit)

        if len(units_batch) >= batch_size:
            transformed_units = list(transform_ous(units_batch, tenant_id))
            load_ous(
                neo4j_session, transformed_units, update_tag, common_job_parameters
            )
            units_batch.clear()

    # Process any remaining OUs
    if units_batch:
        transformed_units = list(transform_ous(units_batch, tenant_id))
        load_ous(neo4j_session, transformed_units, update_tag, common_job_parameters)

    # Cleanup stale data
    cleanup_ous(neo4j_session, common_job_parameters)
