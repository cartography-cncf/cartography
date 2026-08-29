import logging

import neo4j

from cartography.config import Config
from cartography.intel.snyk import issues
from cartography.intel.snyk import orgs
from cartography.intel.snyk import projects
from cartography.intel.snyk import targets
from cartography.intel.snyk.util import build_session
from cartography.intel.snyk.util import DEFAULT_BASE_URL
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_snyk_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.snyk_api_key or not config.snyk_org_id:
        logger.info(
            "Snyk import is not configured - skipping this module. See docs to configure."
        )
        return

    base_url = config.snyk_base_url or DEFAULT_BASE_URL
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ORG_ID": config.snyk_org_id,
    }
    session = build_session(config.snyk_api_key)

    orgs.sync(
        neo4j_session,
        session,
        base_url,
        config.snyk_org_id,
        config.update_tag,
        common_job_parameters,
    )
    targets.sync(
        neo4j_session,
        session,
        base_url,
        common_job_parameters["ORG_ID"],
        config.update_tag,
        common_job_parameters,
    )
    projects.sync(
        neo4j_session,
        session,
        base_url,
        common_job_parameters["ORG_ID"],
        config.update_tag,
        common_job_parameters,
    )
    issues.sync(
        neo4j_session,
        session,
        base_url,
        common_job_parameters["ORG_ID"],
        config.update_tag,
        common_job_parameters,
    )

    # Cleanup runs only after every collection above has completed successfully, so
    # malformed or partial API data cannot drive stale-node deletion.
    issues.cleanup(neo4j_session, common_job_parameters)
    projects.cleanup(neo4j_session, common_job_parameters)
    targets.cleanup(neo4j_session, common_job_parameters)
    orgs.cleanup(neo4j_session, common_job_parameters)
