import logging

import neo4j

from cartography.config import Config
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
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

    # sync_deployment must be called first since it populates common_job_parameters
    # with the deployment ID and slug, which are required by the other sync functions
    sync_deployment(neo4j_session, config.semgrep_app_token, config.update_tag, common_job_parameters)
    sync_dependencies(neo4j_session, config.semgrep_app_token, config.semgrep_dependency_ecosystems, config.update_tag, common_job_parameters)  # noqa: E501
    sync_findings(neo4j_session, config.semgrep_app_token, config.update_tag, common_job_parameters)
