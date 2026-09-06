import logging
from typing import Any

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_namespace_all
from cartography.util.lazy import lazy_submodule

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
get_salesforce_client = lazy_callable(
    "cartography.intel.salesforce.util", "get_salesforce_client"
)
sync_connectedapps = lazy_callable("cartography.intel.salesforce.connectedapps", "sync")
sync_groups = lazy_callable("cartography.intel.salesforce.groups", "sync")
sync_organization = lazy_callable("cartography.intel.salesforce.organization", "sync")
sync_permissionsets = lazy_callable(
    "cartography.intel.salesforce.permissionsets", "sync"
)
sync_profiles = lazy_callable("cartography.intel.salesforce.profiles", "sync")
sync_userroles = lazy_callable("cartography.intel.salesforce.userroles", "sync")
sync_users = lazy_callable("cartography.intel.salesforce.users", "sync")

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

    org = sync_organization(neo4j_session, client, common_job_parameters)
    common_job_parameters["ORG_ID"] = org["Id"]

    # Load permission/role nodes before users so the user relationships
    # (HAS_ROLE -> Profile, MEMBER_OF -> UserRole) attach to fully-loaded nodes.
    sync_profiles(neo4j_session, client, common_job_parameters)
    sync_userroles(neo4j_session, client, common_job_parameters)
    sync_users(neo4j_session, client, common_job_parameters)
    sync_permissionsets(neo4j_session, client, common_job_parameters)
    sync_groups(neo4j_session, client, common_job_parameters)
    sync_connectedapps(neo4j_session, client, common_job_parameters)


# DEPRECATED: importing this package used to populate its namespace with every
# submodule the entry point pulled, so callers could reach a stage through
# `cartography.intel.salesforce.<domain>`. Those imports are lazy now, so the names are served on
# demand instead. Remove in v1.0.0.
def __getattr__(name: str) -> Any:
    return lazy_submodule(__name__, name)


# A star-import only reaches __getattr__ for names __all__ mentions, so the shim above
# needs this to cover `from cartography.intel.salesforce import *` too.
__all__ = lazy_namespace_all(__path__, globals())
