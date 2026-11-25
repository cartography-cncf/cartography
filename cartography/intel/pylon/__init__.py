import logging

import neo4j

import cartography.intel.pylon.organization
import cartography.intel.pylon.roles
import cartography.intel.pylon.teams
import cartography.intel.pylon.users
from cartography.config import Config
from cartography.intel.pylon.util import build_session
from cartography.intel.pylon.util import resolve_base_url
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_pylon_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Pylon data. Otherwise warn
    and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.pylon_api_token:
        logger.info(
            "Pylon import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    base_url = resolve_base_url(config.pylon_api_token, config.pylon_base_url)
    api_session = build_session(config.pylon_api_token)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    org_id = cartography.intel.pylon.organization.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    common_job_parameters["ORG_ID"] = org_id

    # Roles load before users so that HAS_ROLE edges find their targets, and
    # users load before teams so that MEMBER_OF edges find theirs.
    cartography.intel.pylon.roles.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    cartography.intel.pylon.users.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
    cartography.intel.pylon.teams.sync(
        neo4j_session,
        api_session,
        base_url,
        common_job_parameters,
    )
