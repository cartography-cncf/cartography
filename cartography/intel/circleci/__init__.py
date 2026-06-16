import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.circleci.context_env_vars
import cartography.intel.circleci.contexts
import cartography.intel.circleci.organizations
import cartography.intel.circleci.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

# ponytail: Environments/Components (CircleCI Releases API) and org "Groups" are
# intentionally not synced - the former lives on a separate, still-evolving API
# surface and the latter has no public API v2 endpoint. Add them when a concrete
# need exists rather than guessing at response shapes.


@timeit
def start_circleci_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of CircleCI data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.circleci_token:
        logger.info(
            "CircleCI import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Circle-Token": config.circleci_token})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.circleci_base_url,
    }

    # Organizations are the tenant; everything else is scoped under an org.
    orgs = cartography.intel.circleci.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    for org in orgs:
        org_id = org["id"]
        org_job_parameters = {**common_job_parameters, "ORG_ID": org_id}

        cartography.intel.circleci.users.sync(
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        contexts = cartography.intel.circleci.contexts.sync(
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
        )
        cartography.intel.circleci.context_env_vars.sync(
            neo4j_session,
            api_session,
            org_job_parameters,
            org_id,
            contexts,
        )
