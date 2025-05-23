import logging

import neo4j
import requests

import cartography.intel.openai.adminapikeys
import cartography.intel.openai.apikeys
import cartography.intel.openai.projects
import cartography.intel.openai.serviceaccounts
import cartography.intel.openai.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_openai_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of OpenAI data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.openai_apikey or not config.openai_org_id:
        logger.info(
            "OpenAI import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create requests sessions
    api_session = requests.session()
    api_session.headers.update(
        {
            "Authorization": f"Bearer {config.openai_apikey}",
            "OpenAI-Organization": config.openai_org_id,
        }
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.openai.com/v1",
        "ORG_ID": config.openai_org_id,
    }

    # Organization node is created during the users sync
    cartography.intel.openai.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=config.openai_org_id,
    )

    for project in cartography.intel.openai.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=config.openai_org_id,
    ):
        project_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "BASE_URL": "https://api.openai.com/v1",
            "ORG_ID": config.openai_org_id,
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
        ORG_ID=config.openai_org_id,
    )
