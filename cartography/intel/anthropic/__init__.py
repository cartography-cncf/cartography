import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.federation
import cartography.intel.anthropic.organization
import cartography.intel.anthropic.serviceaccounts
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
from cartography.config import Config
from cartography.intel.anthropic.auth import AnthropicAuth
from cartography.intel.anthropic.auth import is_federated
from cartography.intel.anthropic.auth import make_assertion_source
from cartography.intel.anthropic.auth import make_credential
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_anthropic_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Anthropic data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    # Resolve the identity token source first: a Workload Identity Federation setup
    # missing one of its parts is an operator mistake (typo in the flag, unpopulated
    # environment variable) and must fail loudly rather than silently skip the module.
    assertion_source = make_assertion_source(
        config.anthropic_identity_token_file,
        config.anthropic_identity_token_env_var,
    )
    if not config.anthropic_apikey and assertion_source is None:
        logger.info(
            "Anthropic import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    credential = make_credential(
        apikey=config.anthropic_apikey,
        identity_token_file=config.anthropic_identity_token_file,
        identity_token_env_var=config.anthropic_identity_token_env_var,
        federation_rule_id=config.anthropic_federation_rule_id,
        organization_id=config.anthropic_organization_id,
        service_account_id=config.anthropic_service_account_id,
    )

    # Create requests sessions
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.auth = AnthropicAuth(credential)
    api_session.headers.update({"anthropic-version": "2023-06-01"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.anthropic.com/v1",
    }

    # Must run first: it creates the organization node that scopes every other node,
    # and resolves the ORG_ID the remaining syncs read from common_job_parameters.
    cartography.intel.anthropic.organization.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.anthropic.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    cartography.intel.anthropic.workspaces.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Service accounts and federation resources reject Admin API keys with a 403;
    # they are only readable with an org:admin OAuth token. Must run before the API
    # key sync, which edges service-account-owned keys to their principal.
    if is_federated(credential):
        cartography.intel.anthropic.serviceaccounts.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
        )

        cartography.intel.anthropic.federation.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
        )
    else:
        logger.info(
            "Skipping Anthropic service accounts and federation resources: those "
            "endpoints reject Admin API keys. Configure Workload Identity "
            "Federation to ingest them.",
        )

    cartography.intel.anthropic.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
