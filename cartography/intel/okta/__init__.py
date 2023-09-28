import logging
import asyncio
from typing import Dict

import neo4j
from okta.client import Client as OktaClient

from cartography.config import Config

from cartography.intel.okta import applications

from cartography.intel.okta import awssaml
from cartography.intel.okta import authenticators
from cartography.intel.okta import groups
from cartography.intel.okta import organization
from cartography.intel.okta import roles
from cartography.intel.okta import origins

from cartography.intel.okta import users
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def _cleanup_okta_organizations(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Remove stale Okta organization
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job("okta_import_cleanup.json", neo4j_session, common_job_parameters)
    cleanup_okta_groups(neo4j_session, common_job_parameters)


def cleanup_okta_groups(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    run_cleanup_job("okta_groups_cleanup.json", neo4j_session, common_job_parameters)


def _create_okta_client(okta_domain: str, okta_api_key: str) -> OktaClient:
    """
    Create Okta User Client
    :param okta_domain: Okta domain
    :param okta_api_key: Okta API key
    :return: Instance of UsersClient
    """
    config = {"orgUrl": f"https://{okta_domain}/", "token": okta_api_key}
    okta_client = OktaClient(config)

    return okta_client


@timeit
def start_okta_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the OKTA ingestion process
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    if not config.okta_api_key:
        logger.warning(
            "No valid Okta credentials could be found. Exiting Okta sync stage.",
        )
        return

    logger.debug(f"Starting Okta sync on {config.okta_org_id}")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "OKTA_ORG_ID": config.okta_org_id,
    }

    okta_client = _create_okta_client(config.okta_org_id, config.okta_api_key)

    organization.sync_okta_organization(neo4j_session, common_job_parameters)
    users.sync_okta_users(okta_client, neo4j_session, common_job_parameters)
    roles.sync_okta_roles(okta_client, neo4j_session, common_job_parameters)
    groups.sync_okta_groups(okta_client, neo4j_session, common_job_parameters)
    users.sync_okta_user_types(okta_client, neo4j_session, common_job_parameters)
    applications.sync_okta_applications(
        okta_client, neo4j_session, common_job_parameters
    )
    origins.sync_okta_origins(okta_client, neo4j_session, common_job_parameters)
    authenticators.sync_okta_authenticators(
        okta_client, neo4j_session, common_job_parameters
    )

    # TODO: Deprecate this while we determine a method of making it more generic
    # awssaml.sync_okta_aws_saml(
    #    neo4j_session, config.okta_saml_role_regex, config.update_tag
    # )

    _cleanup_okta_organizations(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="OktaOrganization",
        group_id=config.okta_org_id,
        synced_type="OktaOrganization",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
