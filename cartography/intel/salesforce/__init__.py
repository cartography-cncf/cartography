import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.salesforce.organization
import cartography.intel.salesforce.permission_sets
import cartography.intel.salesforce.profiles
import cartography.intel.salesforce.users
from cartography.config import Config
from cartography.intel.salesforce.util import get_access_token_client_credentials
from cartography.intel.salesforce.util import get_access_token_jwt_bearer
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _is_configured(config: Config) -> bool:
    """
    Salesforce ingestion requires an instance URL and a connected app client ID, plus
    the credentials for exactly one supported OAuth flow: either a client secret
    (Client Credentials flow) or a username + private key (JWT Bearer flow).
    """
    if not config.salesforce_instance_url or not config.salesforce_client_id:
        return False
    has_client_credentials = bool(config.salesforce_client_secret)
    has_jwt_bearer = bool(config.salesforce_username and config.salesforce_private_key)
    return has_client_credentials or has_jwt_bearer


def _authenticate(config: Config) -> tuple[str, str]:
    """
    Authenticate using whichever OAuth flow the provided credentials select. The client
    secret takes precedence when both sets of credentials happen to be present.
    """
    if config.salesforce_client_secret:
        logger.info("Authenticating to Salesforce using the Client Credentials flow.")
        return get_access_token_client_credentials(
            config.salesforce_instance_url,
            config.salesforce_client_id,
            config.salesforce_client_secret,
        )
    logger.info("Authenticating to Salesforce using the JWT Bearer flow.")
    return get_access_token_jwt_bearer(
        config.salesforce_instance_url,
        config.salesforce_client_id,
        config.salesforce_username,
        config.salesforce_private_key,
    )


@timeit
def start_salesforce_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Salesforce people and their
    permissions (users, profiles, permission sets). Otherwise warn and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not _is_configured(config):
        logger.info(
            "Salesforce import is not configured - skipping this module. "
            "See docs to configure."
        )
        return

    access_token, instance_url = _authenticate(config)

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {access_token}"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "INSTANCE_URL": instance_url,
    }

    # Organization (tenant) first so its node exists for the RESOURCE sub-resource
    # relationships, then profiles and permission sets so they exist before the user
    # sync wires up HAS_PROFILE / HAS_PERMISSION_SET edges.
    org_id = cartography.intel.salesforce.organization.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    common_job_parameters["ORG_ID"] = org_id

    cartography.intel.salesforce.profiles.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.salesforce.permission_sets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.salesforce.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
