import asyncio
import logging
from collections.abc import Awaitable

import neo4j
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient

from cartography.config import Config
from cartography.intel.microsoft import credentials
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


class DelegatedEntraSyncIncomplete(RuntimeError):
    """Raised after a delegated sync when Graph denied one or more datasets."""

    def __init__(self, denied_datasets: list[str]) -> None:
        self.denied_datasets = tuple(denied_datasets)
        super().__init__(
            "Microsoft Graph denied access to delegated Entra datasets: "
            + ", ".join(denied_datasets),
        )


@timeit
async def sync_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str | None,
    client_secret: str | None,
    update_tag: int,
    *,
    delegated_auth: bool = False,
) -> None:
    """
    Sync tenant information as a prerequisite for all other Entra resource syncs.

    :param neo4j_session: Neo4j session
    :param tenant_id: Entra tenant ID
    :param client_id: Azure application client ID
    :param client_secret: Azure application client secret
    :param update_tag: Update tag for tracking data freshness
    :param delegated_auth: Use the current Azure CLI user
    """
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
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
    delegated_auth = config.microsoft_delegated_auth
    if not tenant_id or (not delegated_auth and (not client_id or not client_secret)):
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
        denied_datasets: list[str] = []

        async def run_dataset(
            name: str,
            operation: Awaitable[None],
            *,
            allow_application_auth_denial: bool = False,
        ) -> None:
            try:
                await operation
            except APIError as e:
                delegated_denial = delegated_auth and e.response_status_code == 403
                optional_denial = (
                    not delegated_auth
                    and allow_application_auth_denial
                    and e.response_status_code in (401, 403)
                )
                if not delegated_denial and not optional_denial:
                    raise
                logger.warning(
                    "Microsoft Graph denied access during Entra %s sync (%d). "
                    "Continuing with the next dataset; collected graph data was preserved.",
                    name,
                    e.response_status_code,
                )
                if delegated_denial:
                    denied_datasets.append(name)

        if delegated_auth:
            logger.warning(
                "Using experimental delegated Entra authentication. Results "
                "reflect only the current user's visibility, may be incomplete, "
                "and will not delete existing Entra data.",
            )

        await sync_tenant(
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            delegated_auth=delegated_auth,
        )

        sync_args = (
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )
        await run_dataset(
            "users",
            sync_entra_users(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "groups",
            sync_entra_groups(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "administrative units",
            sync_entra_ous(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "applications",
            sync_entra_applications(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "service principals",
            sync_service_principals(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "app role assignments",
            sync_app_role_assignments(*sync_args, delegated_auth=delegated_auth),
        )
        await run_dataset(
            "directory roles",
            sync_entra_directory_roles(*sync_args, delegated_auth=delegated_auth),
            allow_application_auth_denial=True,
        )

        # Derived federation cleanup is unsafe when delegated visibility is partial.
        if not delegated_auth:
            await sync_entra_federation(
                neo4j_session,
                config.update_tag,
                tenant_id,
                common_job_parameters,
            )
        else:
            logger.warning(
                "Delegated Entra sync finished with partial-visibility semantics. "
                "Datasets denied by Microsoft Graph: %s.",
                ", ".join(denied_datasets) if denied_datasets else "none",
            )
            if denied_datasets:
                raise DelegatedEntraSyncIncomplete(denied_datasets)

    asyncio.run(main())
