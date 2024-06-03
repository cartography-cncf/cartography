import logging
from typing import Dict

import neo4j
from okta.framework.OktaError import OktaError

from cartography.config import Config
from cartography.intel.okta import applications
from cartography.intel.okta import awssaml
from cartography.intel.okta import factors
from cartography.intel.okta import groups
from cartography.intel.okta import organization
from cartography.intel.okta import origins
from cartography.intel.okta import roles
from cartography.intel.okta import users
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def _cleanup_okta_organizations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove stale Okta organization
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job('okta_import_cleanup.json', neo4j_session, common_job_parameters)
    cleanup_okta_groups(neo4j_session, common_job_parameters)


def cleanup_okta_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('okta_groups_cleanup.json', neo4j_session, common_job_parameters)


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

    state = OktaSyncState()

    organization.create_okta_organization(neo4j_session, config.okta_org_id, config.update_tag)
    users.sync_okta_users(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key, state)
    groups.sync_okta_groups(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key, state)
    applications.sync_okta_applications(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key)
    factors.sync_users_factors(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key, state)
    origins.sync_trusted_origins(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key)
    awssaml.sync_okta_aws_saml(neo4j_session, config.okta_saml_role_regex, config.update_tag, config.okta_org_id)

    # need creds with permission
    # soft fail as some won't be able to get such high priv token
    # when we get the E0000006 error
    # see https://developer.okta.com/docs/reference/error-codes/
    try:
        roles.sync_roles(neo4j_session, config.okta_org_id, config.update_tag, config.okta_api_key, state)
    except OktaError as okta_error:
        logger.warning(f"Unable to pull admin roles got {okta_error}")

        # Getting roles requires super admin which most won't be able to get easily
        if okta_error.error_code == "E0000006":
            logger.warning("Unable to sync admin roles - api token needs admin rights to pull admin roles data")

    _cleanup_okta_organizations(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='OktaOrganization',
        group_id=config.okta_org_id,
        synced_type='OktaOrganization',
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
