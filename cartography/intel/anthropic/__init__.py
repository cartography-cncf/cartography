import logging

import neo4j
import requests

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_anthropic_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Anthropic data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.anthropic_apikey:
        logger.info(
            "Anthropic import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create requests sessions
    api_session = requests.session()
    api_session.headers.update(
        {
            "X-Api-Key": config.anthropic_apikey,
            "anthropic-version": "2023-06-01",
        }
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.anthropic.com/v1",
    }

    # Organization node is created during the users sync
    cartography.intel.anthropic.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.anthropic.workspaces.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.anthropic.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
