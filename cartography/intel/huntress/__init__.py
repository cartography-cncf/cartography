import logging

import neo4j

from cartography.config import Config
from cartography.intel.huntress import account
from cartography.intel.huntress import agents
from cartography.intel.huntress import incident_reports
from cartography.intel.huntress import memberships
from cartography.intel.huntress import organizations
from cartography.intel.huntress.util import create_huntress_api_session
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URI = "https://api.huntress.io"


@timeit
def start_huntress_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:

    if not config.huntress_api_key or not config.huntress_api_secret:
        logger.info(
            "Huntress import is not configured - skipping this module. See docs to configure."
        )
        return

    base_uri = config.huntress_base_uri or DEFAULT_BASE_URI
    api_session = create_huntress_api_session(
        config.huntress_api_key,
        config.huntress_api_secret,
    )
    try:
        # The account is the tenant every other node hangs off, so it is resolved and
        # loaded first; the credentials only ever resolve to one of them.
        account_id = account.sync(
            neo4j_session,
            api_session,
            base_uri,
            config.update_tag,
        )
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ACCOUNT_ID": account_id,
        }
        sync_args = (
            neo4j_session,
            api_session,
            base_uri,
            account_id,
            config.update_tag,
            common_job_parameters,
        )
        # Organizations first: agents, incident reports and memberships all point at them.
        organizations.sync(*sync_args)
        agents.sync(*sync_args)
        # Incident reports point at the agents loaded just above.
        incident_reports.sync(*sync_args)
        memberships.sync(*sync_args)
    finally:
        api_session.close()
