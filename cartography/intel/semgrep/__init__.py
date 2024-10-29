import logging

import neo4j

from cartography.config import Config
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import get_deployment
from cartography.intel.semgrep.deployment import load_semgrep_deployment
from cartography.intel.semgrep.findings import sync_findings
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def start_semgrep_ingestion(
    neo4j_session: neo4j.Session, config: Config,
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.semgrep_app_token:
        logger.info('Semgrep import is not configured - skipping this module. See docs to configure.')
        return

    # fetch and load the Semgrep deployment
    semgrep_deployment = get_deployment(config.semgrep_app_token)
    deployment_id = semgrep_deployment["id"]
    deployment_slug = semgrep_deployment["slug"]
    load_semgrep_deployment(neo4j_session, semgrep_deployment, config.update_tag)
    common_job_parameters["DEPLOYMENT_ID"] = deployment_id
    common_job_parameters["DEPLOYMENT_SLUG"] = deployment_slug

    sync_dependencies(neo4j_session, config.semgrep_app_token, config.update_tag, common_job_parameters)
    sync_findings(neo4j_session, config.semgrep_app_token, config.update_tag, common_job_parameters)
