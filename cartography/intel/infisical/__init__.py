import logging

import neo4j

from cartography.config import Config
from cartography.intel.infisical import api
from cartography.intel.infisical import projects
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_infisical_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """Ingest Infisical project metadata for one organization."""
    if not all(
        (
            config.infisical_api_url,
            config.infisical_organization_id,
            config.infisical_client_id,
            config.infisical_client_secret,
        ),
    ):
        logger.info(
            "Infisical import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    try:
        api_url = api.normalize_api_url(config.infisical_api_url)
    except ValueError as exc:
        logger.warning("Invalid Infisical API URL - skipping this module: %s", exc)
        return

    session = api.create_session(
        api_url,
        config.infisical_client_id,
        config.infisical_client_secret,
    )
    try:
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "INFISICAL_ORGANIZATION_ID": config.infisical_organization_id,
        }
        projects.sync(
            neo4j_session,
            session,
            api_url,
            config.infisical_organization_id,
            config.update_tag,
            common_job_parameters,
        )
    finally:
        session.close()
