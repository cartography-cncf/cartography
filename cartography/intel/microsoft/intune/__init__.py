import asyncio
import logging

import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError

from cartography.config import Config
from cartography.intel.microsoft.client import create_graph_service_client
from cartography.intel.microsoft.intune.compliance_policies import (
    sync_compliance_policies,
)
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps
from cartography.intel.microsoft.intune.managed_devices import sync_managed_devices
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_intune_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of Intune data. Requires Entra sync to have run first,
    as Intune nodes relate back to Entra users, groups, and tenants.

    Uses the same Microsoft Graph credentials as the Entra sync
    (config.entra_tenant_id / client_id / client_secret).
    TODO: rename config params to microsoft_* once CLI migration is done.

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
            "Intune import is not configured - skipping this module. "
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
        intune_client = create_graph_service_client(credential)

        managed_devices_synced = False
        try:
            await sync_managed_devices(
                neo4j_session,
                intune_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
            managed_devices_synced = True
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

        compliance_policies_synced = False
        try:
            await sync_compliance_policies(
                neo4j_session,
                intune_client,
                config.entra_tenant_id,
                config.update_tag,
                common_job_parameters,
            )
            compliance_policies_synced = True
        except APIError as e:
            if e.response_status_code == 403:
                logger.warning(
                    "Skipping Intune compliance policy sync: missing "
                    "DeviceManagementConfiguration.Read.All permission (403).",
                )
            else:
                raise

        # Only run the analysis job when both sides synced successfully.
        # If either side was skipped (403), stale nodes remain without
        # cleanup; running the analysis would refresh APPLIES_TO edges on
        # those stale nodes, preventing their eventual removal.
        if managed_devices_synced and compliance_policies_synced:
            run_scoped_analysis_job(
                "intune_compliance_policy_device.json",
                neo4j_session,
                common_job_parameters,
            )
        else:
            logger.info(
                "Skipping Intune compliance-policy-to-device analysis: "
                "managed_devices_synced=%s, compliance_policies_synced=%s.",
                managed_devices_synced,
                compliance_policies_synced,
            )

    asyncio.run(main())
