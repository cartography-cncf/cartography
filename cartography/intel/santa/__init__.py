import logging

import neo4j

import cartography.intel.santa.events
import cartography.intel.santa.machines
from cartography.config import Config
from cartography.intel.santa.client import ZentralSantaClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_santa_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Santa machine and event data from Zentral.

    :param neo4j_session: Neo4j session for database interface.
    :param config: A cartography.config object.

    :return: None
    """
    if not config.santa_base_url or not config.santa_token:
        logger.info(
            "Santa import is not configured - skipping this module. See docs to configure.",
        )
        return

    if config.santa_event_lookback_days < 0:
        raise ValueError("santa_event_lookback_days must be greater than or equal to 0")

    if config.santa_request_timeout <= 0:
        raise ValueError("santa_request_timeout must be greater than 0")

    source_name = config.santa_source_name or "Santa"

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    client = ZentralSantaClient(
        base_url=config.santa_base_url,
        token=config.santa_token,
        request_timeout=config.santa_request_timeout,
    )

    cartography.intel.santa.machines.sync(
        neo4j_session,
        client,
        source_name,
        common_job_parameters,
    )

    cartography.intel.santa.events.sync(
        neo4j_session,
        client,
        source_name,
        config.santa_event_lookback_days,
        common_job_parameters,
    )
