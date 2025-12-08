import logging

import neo4j

import cartography.intel.ontology.devices
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
        users_source_of_truth = [
            source.strip() for source in config.ontology_users_source.split(",")
        ]
    else:
        users_source_of_truth = []
    if config.ontology_devices_source:
        computers_source_of_truth = [
            source.strip() for source in config.ontology_devices_source.split(",")
        ]
    else:
        computers_source_of_truth = []

    cartography.intel.ontology.users.sync(
        neo4j_session,
        users_source_of_truth,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.devices.sync(
        neo4j_session,
        computers_source_of_truth,
        config.update_tag,
        common_job_parameters,
    )
