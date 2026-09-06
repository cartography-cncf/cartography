import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
migrate_dependency_labels = lazy_callable(
    "cartography.intel.semgrep.label_migrations", "migrate_dependency_labels"
)
sync_dependencies = lazy_callable(
    "cartography.intel.semgrep.dependencies", "sync_dependencies"
)
sync_deployment = lazy_callable(
    "cartography.intel.semgrep.deployment", "sync_deployment"
)
sync_findings = lazy_callable("cartography.intel.semgrep.findings", "sync_findings")
sync_oss_semgrep_sast_findings = lazy_callable(
    "cartography.intel.semgrep.ossfindings", "sync_oss_semgrep_sast_findings"
)
sync_secrets = lazy_callable("cartography.intel.semgrep.secrets", "sync_secrets")

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
        migrate_dependency_labels(
            neo4j_session,
            common_job_parameters["DEPLOYMENT_ID"],
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
        sync_oss_semgrep_sast_findings(
            neo4j_session,
            config.semgrep_oss_source,
            config.update_tag,
            config=config,
        )
