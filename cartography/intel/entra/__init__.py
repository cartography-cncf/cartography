import asyncio
import logging

import neo4j

from cartography.config import Config
from cartography.intel.entra.applications import sync_entra_applications
from cartography.intel.entra.groups import sync_entra_groups
from cartography.intel.entra.ou import sync_entra_ous
from cartography.intel.entra.users import sync_entra_users
from cartography.util import timeit

logger = logging.getLogger(__name__)


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

    # Execute both syncs in sequence
    asyncio.run(main())
