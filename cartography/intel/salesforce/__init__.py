import logging

import neo4j

import cartography.intel.salesforce.connectedapps
import cartography.intel.salesforce.groups
import cartography.intel.salesforce.organization
import cartography.intel.salesforce.permissionsets
import cartography.intel.salesforce.profiles
import cartography.intel.salesforce.userroles
import cartography.intel.salesforce.users
from cartography.config import Config
from cartography.intel.salesforce.util import get_salesforce_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_salesforce_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Salesforce data.
    Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    has_jwt = bool(config.salesforce_username and config.salesforce_private_key)
    has_client_credentials = bool(config.salesforce_client_secret)
    if not config.salesforce_client_id or not (has_jwt or has_client_credentials):
        logger.info(
            "Salesforce import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    client = get_salesforce_client(
        login_url=config.salesforce_login_url,
        client_id=config.salesforce_client_id,
        client_secret=config.salesforce_client_secret,
        username=config.salesforce_username,
        private_key=config.salesforce_private_key,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    org = cartography.intel.salesforce.organization.sync(
        neo4j_session, client, common_job_parameters
    )
    common_job_parameters["ORG_ID"] = org["Id"]

    # Load permission/role nodes before users so the user relationships
    # (HAS_ROLE -> Profile, MEMBER_OF -> UserRole) attach to fully-loaded nodes.
    cartography.intel.salesforce.profiles.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.salesforce.userroles.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.salesforce.users.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.salesforce.permissionsets.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.salesforce.groups.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.salesforce.connectedapps.sync(
        neo4j_session, client, common_job_parameters
    )
