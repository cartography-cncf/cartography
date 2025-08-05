import asyncio
import datetime
import logging
from traceback import TracebackException
from typing import Awaitable
from typing import Callable

import neo4j

from cartography.config import Config
from cartography.intel.entra.resources import RESOURCE_FUNCTIONS
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
        failed_stages = []
        exception_tracebacks = []

        async def run_stage(name: str, func: Callable[..., Awaitable[None]]) -> None:
            try:
                await func(
                    neo4j_session,
                    config.entra_tenant_id,
                    config.entra_client_id,
                    config.entra_client_secret,
                    config.update_tag,
                    common_job_parameters,
                )
            except Exception as e:
                if config.entra_best_effort_mode:
                    timestamp = datetime.datetime.now()
                    failed_stages.append(name)
                    exception_traceback = TracebackException.from_exception(e)
                    traceback_string = "".join(exception_traceback.format())
                    exception_tracebacks.append(
                        f"{timestamp} - Exception for stage {name}\n{traceback_string}"
                    )
                    logger.warning(
                        f"Caught exception syncing {name}. entra-best-effort-mode is on so we are continuing "
                        "on to the next Entra sync. All exceptions will be aggregated and re-logged at the end of the sync.",
                        exc_info=True,
                    )
                else:
                    logger.error("Error during Entra sync", exc_info=True)
                    raise

        for name, func in RESOURCE_FUNCTIONS:
            await run_stage(name, func)

        if failed_stages:
            logger.error(
                f"Entra sync failed for the following stages: {', '.join(failed_stages)}. "
                "See the logs for more details.",
            )
            raise Exception("\n".join(exception_tracebacks))

    # Execute all syncs in sequence
    asyncio.run(main())
