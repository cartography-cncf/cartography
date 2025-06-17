import logging

import neo4j

import cartography.intel.ontology.hosts
import cartography.intel.ontology.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def run(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # WIP: Get source of truth for ontology from config
    USER_SOURCE_OF_TRUTH = ["duo"]
    HOST_SOURCE_OF_TRUTH = ["snipeit"]

    cartography.intel.ontology.hosts.sync(
        neo4j_session,
        HOST_SOURCE_OF_TRUTH,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.users.sync(
        neo4j_session,
        USER_SOURCE_OF_TRUTH,
        config.update_tag,
        common_job_parameters,
    )
