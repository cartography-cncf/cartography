import logging

import neo4j

import cartography.intel.ontology.clientcomputers
import cartography.intel.ontology.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def run(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Get source of truth from config
    if config.ontology_users_source:
        users_source_of_truth = config.ontology_users_source.split(",")
    else:
        logger.warning(
            "No source of truth for users defined in config. No `User` nodes will be created."
        )
        users_source_of_truth = []
    if config.ontology_clientcomputers_source:
        computers_source_of_truth = config.ontology_clientcomputers_source.split(",")
    else:
        logger.warning(
            "No source of truth for client computers defined in config. No `ClientComputer` nodes will be created."
        )
        computers_source_of_truth = []

    cartography.intel.ontology.users.sync(
        neo4j_session,
        users_source_of_truth,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.clientcomputers.sync(
        neo4j_session,
        computers_source_of_truth,
        config.update_tag,
        common_job_parameters,
    )
