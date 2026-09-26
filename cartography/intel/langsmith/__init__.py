import logging

import neo4j

import cartography.intel.langsmith.agent_auth
import cartography.intel.langsmith.apikeys
import cartography.intel.langsmith.deployments
import cartography.intel.langsmith.organizations
import cartography.intel.langsmith.roles
import cartography.intel.langsmith.sso
import cartography.intel.langsmith.users
import cartography.intel.langsmith.workspace_resources
import cartography.intel.langsmith.workspaces
from cartography.config import Config
from cartography.intel.langsmith.util import LangSmithClient
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Defaults for the LangSmith SaaS. The CLI supplies these too; they are repeated here so a
# Config built directly in code still points somewhere valid.
DEFAULT_API_URL = "https://api.smith.langchain.com"
DEFAULT_HOST_API_URL = "https://api.host.langchain.com"


@timeit
def start_langsmith_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of LangSmith data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.langsmith_pat:
        logger.info(
            "LangSmith import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    client = LangSmithClient(
        pat=config.langsmith_pat,
        api_url=config.langsmith_api_url or DEFAULT_API_URL,
        host_api_url=config.langsmith_host_api_url or DEFAULT_HOST_API_URL,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    organizations = cartography.intel.langsmith.organizations.sync(
        neo4j_session,
        client,
        config.langsmith_org_id,
        common_job_parameters,
    )

    for organization in organizations:
        org_id = organization["id"]
        logger.info("Starting LangSmith ingestion for organization %s", org_id)
        org_common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ORG_ID": org_id,
        }

        # Roles and permissions come first: memberships, keys, SSO settings and access
        # policies all point at them.
        cartography.intel.langsmith.roles.sync(
            neo4j_session, client, org_id, org_common_job_parameters
        )

        workspaces = cartography.intel.langsmith.workspaces.sync(
            neo4j_session, client, org_id, org_common_job_parameters
        )
        workspace_ids = [workspace["id"] for workspace in workspaces]

        users = cartography.intel.langsmith.users.sync(
            neo4j_session, client, org_id, workspace_ids, org_common_job_parameters
        )

        cartography.intel.langsmith.apikeys.sync(
            neo4j_session, client, org_id, users, workspaces, org_common_job_parameters
        )

        cartography.intel.langsmith.sso.sync(
            neo4j_session, client, org_id, org_common_job_parameters
        )

        agents, _, deployments_complete = cartography.intel.langsmith.deployments.sync(
            neo4j_session, client, org_id, workspaces, org_common_job_parameters
        )

        cartography.intel.langsmith.agent_auth.sync(
            neo4j_session,
            client,
            org_id,
            workspaces,
            agents,
            users,
            deployments_complete,
            org_common_job_parameters,
        )

        cartography.intel.langsmith.workspace_resources.sync(
            neo4j_session, client, org_id, workspaces, org_common_job_parameters
        )

    logger.info("Completed LangSmith sync")
