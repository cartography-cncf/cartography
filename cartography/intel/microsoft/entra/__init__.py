import asyncio
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from functools import partial

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


async def _run_dataset(
    name: str,
    operation: Awaitable[None],
    *,
    allowed_statuses: tuple[int, ...],
) -> bool:
    try:
        await operation
    except APIError as e:
        if e.response_status_code not in allowed_statuses:
            raise
        logger.warning(
            "Skipping Entra %s sync because Microsoft Graph denied access (%d). "
            "Existing graph data was preserved.",
            name,
            e.response_status_code,
        )
        return False
    return True


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
        skipped_datasets: list[str] = []
        if delegated_auth:
            logger.warning(
                "Using experimental delegated Entra authentication. Results "
                "reflect only the current user's visibility, may be incomplete, "
                "and will not delete existing Entra data.",
            )

        common_args = (
            neo4j_session,
            tenant_id,
            client_id,
            client_secret,
            config.update_tag,
            common_job_parameters,
        )
        delegated_denials = (403,) if delegated_auth else ()
        datasets: list[tuple[str, Callable[[], Awaitable[None]], tuple[int, ...]]] = [
            (
                "tenant",
                partial(
                    sync_tenant,
                    *common_args[:-1],
                    delegated_auth=delegated_auth,
                ),
                delegated_denials,
            ),
            (
                "users",
                partial(sync_entra_users, *common_args, delegated_auth=delegated_auth),
                delegated_denials,
            ),
            (
                "groups",
                partial(sync_entra_groups, *common_args, delegated_auth=delegated_auth),
                delegated_denials,
            ),
            (
                "administrative units",
                partial(sync_entra_ous, *common_args, delegated_auth=delegated_auth),
                delegated_denials,
            ),
            (
                "applications",
                partial(
                    sync_entra_applications, *common_args, delegated_auth=delegated_auth
                ),
                delegated_denials,
            ),
            (
                "service principals",
                partial(
                    sync_service_principals, *common_args, delegated_auth=delegated_auth
                ),
                delegated_denials,
            ),
            (
                "app role assignments",
                partial(
                    sync_app_role_assignments,
                    *common_args,
                    delegated_auth=delegated_auth,
                ),
                delegated_denials,
            ),
            # Directory roles remain optional for application auth too.
            (
                "directory roles",
                partial(
                    sync_entra_directory_roles,
                    *common_args,
                    delegated_auth=delegated_auth,
                ),
                (403,) if delegated_auth else (401, 403),
            ),
        ]
        for name, sync_dataset, allowed_statuses in datasets:
            if not await _run_dataset(
                name,
                sync_dataset(),
                allowed_statuses=allowed_statuses,
            ):
                skipped_datasets.append(name)

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
                ", ".join(skipped_datasets) if skipped_datasets else "none",
            )

    asyncio.run(main())
