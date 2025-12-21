import logging

import neo4j

from cartography.config import Config
from cartography.intel.gitlab import repositories
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_gitlab_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of GitLab data. Otherwise warn and exit.

    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not all(
        [
            config.gitlab_url,
            config.gitlab_token,
        ],
    ):
        logger.info(
            "GitLab import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    repositories.sync_gitlab_repositories(
        neo4j_session,
        config.gitlab_url,
        config.gitlab_token,
        config.update_tag,
    )
