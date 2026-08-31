import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.unikraft.account
import cartography.intel.unikraft.certificates
import cartography.intel.unikraft.instances
import cartography.intel.unikraft.service_groups
import cartography.intel.unikraft.volumes
from cartography.config import Config
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_tracked_count
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_unikraft_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Unikraft Cloud data. Otherwise skip.
    """
    if not config.unikraft_token:
        logger.info(
            "Unikraft import is not configured - skipping this module. "
            "Set unikraft_token to enable the Unikraft sync stage.",
        )
        return

    session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update({"Authorization": f"Bearer {config.unikraft_token}"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Account quotas are metro-independent, so any base URL works here.
    account_base_url = next(iter(METRO_BASE_URLS.values()))
    account_id, expected_counts = cartography.intel.unikraft.account.sync(
        neo4j_session,
        session,
        account_base_url,
        config.update_tag,
    )
    common_job_parameters["ACCOUNT_ID"] = account_id
    cartography.intel.unikraft.account.cleanup(neo4j_session, common_job_parameters)

    cartography.intel.unikraft.instances.sync(
        neo4j_session,
        session,
        account_id,
        config.update_tag,
        common_job_parameters,
        require_tracked_count(expected_counts, "instances"),
    )
    cartography.intel.unikraft.volumes.sync(
        neo4j_session,
        session,
        account_id,
        config.update_tag,
        common_job_parameters,
        require_tracked_count(expected_counts, "volumes"),
    )
    cartography.intel.unikraft.certificates.sync(
        neo4j_session,
        session,
        account_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.unikraft.service_groups.sync(
        neo4j_session,
        session,
        account_id,
        config.update_tag,
        common_job_parameters,
        require_tracked_count(expected_counts, "service_groups"),
    )
