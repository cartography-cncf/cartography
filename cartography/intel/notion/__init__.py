import logging

import neo4j

from cartography.config import Config
from cartography.intel.notion import scim
from cartography.intel.notion import users
from cartography.intel.notion import workspaces
from cartography.intel.notion.util import create_api_session
from cartography.intel.notion.util import create_scim_session
from cartography.intel.notion.util import parse_config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_notion_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.notion_config:
        logger.info(
            "Notion import is not configured - skipping this module. See docs to configure.",
        )
        return

    workspace_configs = parse_config(config.notion_config)
    for workspace in workspace_configs:
        logger.info("Starting Notion sync for workspace %s", workspace.workspace_id)
        api_session = create_api_session(workspace.api_token)
        try:
            workspaces.sync(
                neo4j_session,
                workspace.workspace_id,
                workspace.workspace_name,
                config.update_tag,
            )
            common_job_parameters = {
                "UPDATE_TAG": config.update_tag,
                "WORKSPACE_ID": workspace.workspace_id,
            }
            public_people = users.sync(
                neo4j_session,
                api_session,
                workspace.workspace_id,
                config.update_tag,
                common_job_parameters,
            )
            if workspace.scim_token:
                scim_session = create_scim_session(workspace.scim_token)
                try:
                    scim.sync(
                        neo4j_session,
                        scim_session,
                        public_people,
                        workspace.workspace_id,
                        config.update_tag,
                        common_job_parameters,
                    )
                finally:
                    scim_session.close()
        finally:
            api_session.close()
        logger.info("Completed Notion sync for workspace %s", workspace.workspace_id)
