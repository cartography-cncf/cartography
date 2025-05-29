import logging

import neo4j
import requests

import cartography.intel.openai.adminapikeys
import cartography.intel.openai.apikeys
import cartography.intel.openai.projects
import cartography.intel.openai.serviceaccounts
import cartography.intel.openai.users
from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_openai_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of OpenAI data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (Deprecated: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("OpenAI", ["apikey", "org_id"]):
        return

    # Create requests sessions
    api_session = requests.session()
    api_session.headers.update(
        {
            "Authorization": f"Bearer {settings.openai.apikey}",
            "OpenAI-Organization": settings.openai.org_id,
        }
    )

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "BASE_URL": "https://api.openai.com/v1",
        "ORG_ID": settings.openai.org_id,
    }

    # Organization node is created during the users sync
    cartography.intel.openai.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=settings.openai.org_id,
    )

    for project in cartography.intel.openai.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=settings.openai.org_id,
    ):
        project_job_parameters = {
            "UPDATE_TAG": settings.common.update_tag,
            "BASE_URL": "https://api.openai.com/v1",
            "ORG_ID": settings.openai.org_id,
            "project_id": project["id"],
        }
        cartography.intel.openai.serviceaccounts.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project["id"],
        )
        cartography.intel.openai.apikeys.sync(
            neo4j_session,
            api_session,
            project_job_parameters,
            project_id=project["id"],
        )

    cartography.intel.openai.adminapikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=settings.openai.org_id,
    )
