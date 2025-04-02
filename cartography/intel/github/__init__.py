import logging

import neo4j
from requests import exceptions

import cartography.intel.github.repos
import cartography.intel.github.teams
import cartography.intel.github.users
from cartography.settings import settings
from cartography.settings import check_module_settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_github_ingestion(neo4j_session: neo4j.Session) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :return: None
    """
    if not check_module_settings('GitHub', ['token', 'url', 'name'], multi_tenant=True):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }
    # run sync for the provided github tokens

    for org_name, auth_data in settings.github.items():
        try:
            cartography.intel.github.users.sync(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                org_name,
            )
            cartography.intel.github.repos.sync(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                org_name,
            )
            cartography.intel.github.teams.sync_github_teams(
                neo4j_session,
                common_job_parameters,
                auth_data.token,
                auth_data.url,
                org_name,
            )
        except exceptions.RequestException as e:
            logger.error("Could not complete request to the GitHub API: %s", e)
