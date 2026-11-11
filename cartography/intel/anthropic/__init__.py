import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
from cartography.config import Config
from cartography.intel.anthropic.auth import WorkloadIdentityAuth
from cartography.intel.anthropic.auth import WorkloadIdentityFederation
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

    federation = _workload_identity_federation(config)
    if not config.anthropic_apikey and federation is None:
        logger.info(
            "Anthropic import is not configured - skipping this module. "
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
    api_session.headers.update({"anthropic-version": "2023-06-01"})
    if federation is not None:
        api_session.auth = WorkloadIdentityAuth(federation)
    else:
        api_session.headers["X-Api-Key"] = config.anthropic_apikey

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.anthropic.com/v1",
    }

    # Organization node is created during the users sync
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

    cartography.intel.anthropic.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )


def _workload_identity_federation(
    config: Config,
) -> WorkloadIdentityFederation | None:
    token_file = config.anthropic_identity_token_file
    rule_id = config.anthropic_federation_rule_id
    organization_id = config.anthropic_organization_id
    service_account_id = config.anthropic_service_account_id
    if not (
        token_file
        or rule_id
        or organization_id
        or service_account_id
        or config.anthropic_workspace_id
    ):
        return None
    if config.anthropic_apikey:
        raise ValueError(
            "Configure Anthropic with an Admin API key or workload identity "
            "federation, not both.",
        )
    if not (token_file and rule_id and organization_id and service_account_id):
        raise ValueError(
            "Anthropic workload identity federation needs an identity token file, "
            "a federation rule ID, an organization ID, and a service account ID.",
        )
    return WorkloadIdentityFederation(
        identity_token_file=token_file,
        federation_rule_id=rule_id,
        organization_id=organization_id,
        service_account_id=service_account_id,
        workspace_id=config.anthropic_workspace_id,
    )
