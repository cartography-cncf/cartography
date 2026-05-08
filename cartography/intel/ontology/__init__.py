import logging

import neo4j

import cartography.intel.ontology.devices
import cartography.intel.ontology.dnsrecords
import cartography.intel.ontology.loadbalancers
import cartography.intel.ontology.packages
import cartography.intel.ontology.publicips
import cartography.intel.ontology.users
from cartography.config import Config
from cartography.util import run_analysis_job
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
    cartography.intel.ontology.dnsrecords.sync(
        neo4j_session,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.loadbalancers.sync(
        neo4j_session,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.packages.sync(
        neo4j_session,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        config.update_tag,
        common_job_parameters,
    )
    # Create RESOLVED_IMAGE edges from :Container to the concrete single-platform :Image they are running.
    # Runs last so the :Container / :Image semantic labels and HAS_IMAGE edges from every provider are in place.
    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
    # Create RUNS_ON shortcut edges from :AIBOMSource to :Container by joining through the shared :Image.
    # Runs after resolved_image_analysis so all semantic labels and HAS_IMAGE edges are in place.
    run_analysis_job(
        "aibom_runs_on_container_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
