import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.config import Config
from cartography.intel.railway.queries import ME_QUERY
from cartography.intel.railway.utils import call_railway_api
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://backboard.railway.com/graphql/v2"


def _build_api_session(token: str) -> requests.Session:
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        # Railway's API is GraphQL over POST, so POST must be retryable. Leaving the urllib3
        # default of idempotent-methods-only would silently disable retries entirely.
        allowed_methods=["POST"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {token}"})
    return api_session


@timeit
def get_workspace_ids(
    api_session: requests.Session,
    base_url: str,
    configured_workspace_id: str | None,
) -> list[str]:
    """
    Resolve which workspaces to sync.

    Railway rejects `projects` queries that omit a workspaceId, so a workspace is the
    mandatory root of every sync. When the operator did not pin one, discover them from the
    token holder's account.
    """
    if configured_workspace_id:
        return [configured_workspace_id]
    data = call_railway_api(api_session, base_url, ME_QUERY)
    return [workspace["id"] for workspace in data["me"]["workspaces"]]


@timeit
def start_railway_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Railway data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.railway_token:
        logger.info(
            "Railway import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = _build_api_session(config.railway_token)
    base_url = config.railway_base_url or DEFAULT_BASE_URL

    workspace_ids = get_workspace_ids(
        api_session,
        base_url,
        config.railway_workspace_id,
    )
    if not workspace_ids:
        logger.warning("Railway token has access to no workspaces - nothing to sync.")
        return

    for workspace_id in workspace_ids:
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "BASE_URL": base_url,
            "WORKSPACE_ID": workspace_id,
        }
        logger.info("Syncing Railway workspace %s", workspace_id)
        _sync_workspace(
            neo4j_session,
            api_session,
            common_job_parameters,
            config.update_tag,
        )


def _sync_workspace(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict,
    update_tag: int,
) -> None:
    # Domain syncs are wired in here as they land.
    return None
