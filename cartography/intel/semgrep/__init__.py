import logging

import neo4j

from cartography.config import Config
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
from cartography.intel.semgrep.findings import sync_findings
from cartography.intel.semgrep.ossfindings import sync_oss_semgrep_sast_findings
from cartography.intel.semgrep.secrets import sync_secrets
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_semgrep_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if config.semgrep_app_token is None and config.semgrep_oss_source is None:
        logger.info(
            "Semgrep import is not configured - skipping this module. See docs to configure.",
        )
        return

    if config.semgrep_app_token:
        # sync_deployment must be called first since it populates common_job_parameters
        # with the deployment ID and slug, which are required by the other sync functions
        sync_deployment(
            neo4j_session,
            config.semgrep_app_token,
            config.update_tag,
            common_job_parameters,
        )
        sync_dependencies(
            neo4j_session,
            config.semgrep_app_token,
            config.semgrep_dependency_ecosystems,
            config.update_tag,
            common_job_parameters,
        )  # noqa: E501
        sync_findings(
            neo4j_session,
            config.semgrep_app_token,
            config.update_tag,
            common_job_parameters,
        )
        sync_secrets(
            neo4j_session,
            config.semgrep_app_token,
            config.update_tag,
            common_job_parameters,
        )

    if config.semgrep_oss_source is not None:
        source = parse_report_source(config.semgrep_oss_source)
        with build_report_reader_for_source(
            source,
            azure_sp_auth=config.azure_sp_auth,
            azure_tenant_id=config.azure_tenant_id,
            azure_client_id=config.azure_client_id,
            azure_client_secret=config.azure_client_secret,
        ) as reader:
            sync_oss_semgrep_sast_findings(
                neo4j_session,
                reader,
                config.update_tag,
                common_job_parameters,
            )
