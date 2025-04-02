import logging

import neo4j

from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
from cartography.intel.semgrep.findings import sync_findings
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def start_semgrep_ingestion(neo4j_session: neo4j.Session) -> None:
    if not check_module_settings('Semgrep', ['token', 'dependency_ecosystems']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }

    # sync_deployment must be called first since it populates common_job_parameters
    # with the deployment ID and slug, which are required by the other sync functions
    sync_deployment(neo4j_session, settings.semgrep.token, settings.common.update_tag, common_job_parameters)
    sync_dependencies(neo4j_session, settings.semgrep.token, settings.semgrep.dependency_ecosystems, settings.common.update_tag, common_job_parameters)  # noqa: E501
    sync_findings(neo4j_session, settings.semgrep.token, settings.common.update_tag, common_job_parameters)
