import logging
from typing import Optional

import neo4j
from requests import exceptions

import cartography.intel.github.repos
import cartography.intel.github.teams
import cartography.intel.github.users
from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_github_ingestion(
    neo4j_session: neo4j.Session, config: Optional[Config] = None
) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: Configuration object for Cartography (DEPRECATED: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("GitHub", ["token", "url", "name"], multi_tenant=True):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }
    # run sync for the provided github tokens

    for auth_data in settings.github.values():
        try:
            cartography.intel.github.users.sync(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                auth_data.name,
            )
            cartography.intel.github.repos.sync(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                auth_data.name,
            )
            cartography.intel.github.teams.sync_github_teams(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                auth_data.name,
            )
        except exceptions.RequestException as e:
            logger.error("Could not complete request to the GitHub API: %s", e)
