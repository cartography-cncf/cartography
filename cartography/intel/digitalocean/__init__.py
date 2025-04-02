import logging

import neo4j
from digitalocean import Manager

from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.intel.digitalocean import compute
from cartography.intel.digitalocean import management
from cartography.intel.digitalocean import platform
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def start_digitalocean_ingestion(neo4j_session: neo4j.Session, _: Config) -> None:
    """
    If this module is configured, perform ingestion of DigitalOcean  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (DEPRECATED)
    :return: None
    """

    if not check_module_settings('DigitalOcean', ['token']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }
    manager = Manager(token=settings.digitalocean.token)

    """
    Get Account ID related to this credentials and pass it along in `common_job_parameters` to avoid cleaning up other
    accounts resources
    """
    account = manager.get_account()
    common_job_parameters["DO_ACCOUNT_ID"] = account.uuid

    platform.sync(neo4j_session, account, settings.common.update_tag, common_job_parameters)
    project_resources = management.sync(neo4j_session, manager, settings.common.update_tag, common_job_parameters)
    compute.sync(neo4j_session, manager, project_resources, settings.common.update_tag, common_job_parameters)
    return
