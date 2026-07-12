import asyncio
import logging

import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError

from cartography.config import Config
from cartography.intel.microsoft.client import create_graph_service_client
from cartography.intel.microsoft.o365.license_details import sync_user_license_details
from cartography.intel.microsoft.o365.licenses import sync_licenses
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_o365_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Sync Office 365 licensing data (subscribed SKUs, service plans, and
    per-user license assignments).

    Requires the same Entra credentials used for the main Microsoft module.
    Needs Organization.Read.All or Directory.Read.All Graph permission for
    subscribedSkus, and User.Read.All or Directory.Read.All for per-user
    license details.

    This sync is optional: if the app registration lacks the required Graph
    permissions, a 401/403 is caught and the sync is skipped gracefully.

    :param neo4j_session: Neo4j session
    :param config: Cartography config with Entra credentials
    """
    if (
        not config.entra_tenant_id
        or not config.entra_client_id
        or not config.entra_client_secret
    ):
        logger.info(
            "O365 import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.entra_tenant_id,
    }

    async def main() -> None:
        credential = ClientSecretCredential(
            tenant_id=config.entra_tenant_id,
            client_id=config.entra_client_id,
            client_secret=config.entra_client_secret,
        )
        o365_client = create_graph_service_client(credential)

        try:
            # Sync tenant-level licenses and service plans
            await sync_licenses(
                neo4j_session,
                o365_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
        except APIError as e:
            if e.response_status_code in (401, 403):
                logger.warning(
                    "Skipping O365 license sync due to insufficient Microsoft "
                    "Graph permissions (Organization.Read.All or "
                    "Directory.Read.All required): %s",
                    e,
                )
                return
            raise

        try:
            # Sync per-user license assignments (depends on licenses loaded above)
            await sync_user_license_details(
                neo4j_session,
                o365_client,
                config.entra_tenant_id,
                config.update_tag,
            )
        except APIError as e:
            if e.response_status_code in (401, 403):
                logger.warning(
                    "Skipping O365 per-user license detail sync due to "
                    "insufficient Microsoft Graph permissions "
                    "(User.Read.All or Directory.Read.All required): %s",
                    e,
                )
            else:
                raise

    asyncio.run(main())
