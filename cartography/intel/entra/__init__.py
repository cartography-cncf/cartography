import asyncio
import logging

import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient

from cartography.config import Config
from cartography.intel.entra.app_role_assignments import sync_app_role_assignments
from cartography.intel.entra.applications import sync_entra_applications
from cartography.intel.entra.federation.aws_identity_center import sync_entra_federation
from cartography.intel.entra.groups import sync_entra_groups
from cartography.intel.entra.intune.compliance_policies import sync_compliance_policies
from cartography.intel.entra.intune.detected_apps import sync_detected_apps
from cartography.intel.entra.intune.managed_devices import sync_managed_devices
from cartography.intel.entra.ou import sync_entra_ous
from cartography.intel.entra.service_principals import sync_service_principals
from cartography.intel.entra.users import get_tenant
from cartography.intel.entra.users import load_tenant
from cartography.intel.entra.users import sync_entra_users
from cartography.intel.entra.users import transform_tenant
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
) -> None:
    """
    Sync tenant information as a prerequisite for all other Entra resource syncs.

    :param neo4j_session: Neo4j session
    :param tenant_id: Entra tenant ID
    :param client_id: Azure application client ID
    :param client_secret: Azure application client secret
    :param update_tag: Update tag for tracking data freshness
    """
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Fetch tenant and load it
    tenant = await get_tenant(client)
    transformed_tenant = transform_tenant(tenant, tenant_id)
    load_tenant(neo4j_session, transformed_tenant, update_tag)


@timeit
def start_entra_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Entra data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if (
        not config.entra_tenant_id
        or not config.entra_client_id
        or not config.entra_client_secret
    ):
        logger.info(
            "Entra import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.entra_tenant_id,
    }

    async def main() -> None:
        # Load tenant first as a prerequisite for all resource syncs
        await sync_tenant(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
        )

        # Run user sync
        await sync_entra_users(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run group sync
        await sync_entra_groups(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run OU sync
        await sync_entra_ous(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run application sync
        await sync_entra_applications(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run service principals sync
        await sync_service_principals(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run app role assignments sync
        await sync_app_role_assignments(
            neo4j_session,
            config.entra_tenant_id,
            config.entra_client_id,
            config.entra_client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run federation sync (after all resources are synced)
        await sync_entra_federation(
            neo4j_session,
            config.update_tag,
            config.entra_tenant_id,
            common_job_parameters,
        )

        # Run Intune syncs (uses same credentials)
        credential = ClientSecretCredential(
            tenant_id=config.entra_tenant_id,
            client_id=config.entra_client_id,
            client_secret=config.entra_client_secret,
        )
        intune_client = GraphServiceClient(
            credential,
            scopes=["https://graph.microsoft.com/.default"],
        )

        intune_managed_devices_synced = False
        try:
            await sync_managed_devices(
                neo4j_session,
                intune_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
            intune_managed_devices_synced = True
        except APIError as e:
            if e.response_status_code == 403:
                logger.warning(
                    "Skipping Intune managed device sync: missing "
                    "DeviceManagementManagedDevices.Read.All permission (403).",
                )
            else:
                raise

        try:
            await sync_detected_apps(
                neo4j_session,
                intune_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
        except APIError as e:
            if e.response_status_code == 403:
                logger.warning(
                    "Skipping Intune detected app sync: missing "
                    "DeviceManagementManagedDevices.Read.All permission (403).",
                )
            else:
                raise

        intune_compliance_policies_synced = False
        try:
            await sync_compliance_policies(
                neo4j_session,
                intune_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
            intune_compliance_policies_synced = True
        except APIError as e:
            if e.response_status_code == 403:
                logger.warning(
                    "Skipping Intune compliance policy sync: missing "
                    "DeviceManagementConfiguration.Read.All permission (403).",
                )
            else:
                raise

        # Resolve compliance policy -> device edges only if both sides were synced
        if intune_managed_devices_synced and intune_compliance_policies_synced:
            run_analysis_job(
                "intune_compliance_policy_device.json",
                neo4j_session,
                common_job_parameters,
            )

    # Execute syncs in sequence
    asyncio.run(main())
