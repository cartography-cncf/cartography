import logging

import neo4j
import requests

from cartography.config import Config
from cartography.intel.jfrog import repositories
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_jfrog_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.jfrog_artifactory_base_url or not config.jfrog_artifactory_token:
        logger.info(
            "JFrog Artifactory import is not configured - skipping this module. "
            "Set --jfrog-artifactory-base-url and --jfrog-artifactory-token-env-var.",
        )
        return

    tenant_id = config.jfrog_artifactory_tenant_id or config.jfrog_artifactory_base_url
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
    }

    api_session = requests.Session()
    api_session.headers.update(
        {
            "Authorization": f"Bearer {config.jfrog_artifactory_token}",
            "Accept": "application/json",
        }
    )

    repositories.sync(
        neo4j_session,
        api_session,
        config.jfrog_artifactory_base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )
