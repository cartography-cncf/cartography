import asyncio
import logging

import neo4j
from azure.identity import ClientSecretCredential
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient

from cartography.config import Config
from cartography.intel.microsoft.entra.app_role_assignments import (
    sync_app_role_assignments,
)
from cartography.intel.microsoft.entra.applications import sync_entra_applications
from cartography.intel.microsoft.entra.directory_roles import sync_entra_directory_roles
from cartography.intel.microsoft.entra.federation.aws_identity_center import (
    sync_entra_federation,
)
from cartography.intel.microsoft.entra.groups import sync_entra_groups
from cartography.intel.microsoft.entra.ou import sync_entra_ous
from cartography.intel.microsoft.entra.service_principals import sync_service_principals
from cartography.intel.microsoft.entra.users import get_tenant
from cartography.intel.microsoft.entra.users import load_tenant
from cartography.intel.microsoft.entra.users import sync_entra_users
from cartography.intel.microsoft.entra.users import transform_tenant
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
    Perform ingestion of Entra identity data (users, groups, OUs, applications,
    service principals, app role assignments, federation).

    Must run before Intune ingestion, as Intune nodes relate back to Entra
    users, groups, and tenants.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    tenant_id = config.microsoft_tenant_id
    client_id = config.microsoft_client_id
    client_secret = config.microsoft_client_secret
    if not tenant_id or not client_id or not client_secret:
        logger.info(
            "Entra import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
    }

    async def main() -> None:
        # Load tenant first as a prerequisite for all resource syncs
        await sync_tenant(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
        )

        # Run user sync
        await sync_entra_users(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run group sync
        await sync_entra_groups(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run OU sync
        await sync_entra_ous(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run application sync
        await sync_entra_applications(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run service principals sync
        await sync_service_principals(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run app role assignments sync
        await sync_app_role_assignments(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )

        # Run directory role sync (definitions + assignments).
        # This requires the RoleManagement.Read.Directory Graph permission, which
        # existing app registrations may not have granted. Treat it as an optional
        # dataset: only an authorization/permission denial is swallowed so the rest
        # of the Entra ingestion (already-loaded users/groups/etc.) is not aborted.
        # Other Graph API errors are re-raised so real failures stay visible.
        try:
            await sync_entra_directory_roles(
                neo4j_session,
                tenant_id,
                client_id,
                client_secret,
                config.update_tag,
                common_job_parameters,
            )
        except APIError as e:
            if e.response_status_code in (401, 403):
                logger.warning(
                    "Skipping Entra directory role sync due to insufficient "
                    "Microsoft Graph permissions (RoleManagement.Read.Directory "
                    "is required): %s",
                    e,
                )
            else:
                raise

        # Run federation sync (after all resources are synced)
        await sync_entra_federation(
            neo4j_session,
            config.update_tag,
            tenant_id,
            common_job_parameters,
        )

    asyncio.run(main())
