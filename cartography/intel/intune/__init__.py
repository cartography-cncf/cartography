import asyncio
import logging

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

from cartography.config import Config
from cartography.intel.intune.compliance_policies import sync_compliance_policies
from cartography.intel.intune.detected_apps import sync_detected_apps
from cartography.intel.intune.managed_devices import sync_managed_devices
from cartography.intel.intune.tenant import sync_tenant
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_intune_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Intune data. Otherwise warn and exit.
    """
    if (
        not config.entra_tenant_id
        or not config.entra_client_id
        or not config.entra_client_secret
    ):
        logger.info(
            "Intune import is not configured - skipping this module. "
            "Intune uses the same Entra credentials (entra_tenant_id, "
            "entra_client_id, entra_client_secret). See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.entra_tenant_id,
    }

    credential = ClientSecretCredential(
        tenant_id=config.entra_tenant_id,
        client_id=config.entra_client_id,
        client_secret=config.entra_client_secret,
    )
    client = GraphServiceClient(
        credential,
        scopes=["https://graph.microsoft.com/.default"],
    )

    async def main() -> None:
        await sync_tenant(neo4j_session, client, config.update_tag)

        await sync_managed_devices(
            neo4j_session,
            client,
            config.entra_tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        await sync_detected_apps(
            neo4j_session,
            client,
            config.entra_tenant_id,
            config.update_tag,
            common_job_parameters,
        )

        await sync_compliance_policies(
            neo4j_session,
            client,
            config.entra_tenant_id,
            config.update_tag,
            common_job_parameters,
        )

    asyncio.run(main())
