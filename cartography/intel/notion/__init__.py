import logging

import neo4j

from cartography.config import Config
from cartography.intel.notion import pages
from cartography.intel.notion import users
from cartography.intel.notion import workspaces
from cartography.intel.notion.util import create_api_session
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
    discovered_workspaces = []
    api_sessions = []
    seen_workspace_ids: set[str] = set()
    try:
        # Discover and validate every workspace before writing any graph data.
        for workspace_config in workspace_configs:
            api_session = create_api_session(workspace_config.api_token)
            api_sessions.append(api_session)
            token_user = workspaces.get(api_session)
            workspace = workspaces.transform(token_user)
            workspace_id = workspace["id"]
            if workspace_id in seen_workspace_ids:
                raise ValueError(
                    "Multiple Notion tokens resolved to the same workspace"
                )
            seen_workspace_ids.add(workspace_id)
            workspace["token_user"] = token_user
            workspace["sync_public_pages"] = workspace_config.sync_public_pages
            discovered_workspaces.append((workspace, api_session))

        for workspace, api_session in discovered_workspaces:
            logger.info("Starting Notion workspace sync")
            workspaces.sync(
                neo4j_session,
                workspace,
                config.update_tag,
            )
            common_job_parameters = {
                "UPDATE_TAG": config.update_tag,
                "WORKSPACE_ID": workspace["id"],
            }
            users.sync(
                neo4j_session,
                api_session,
                workspace,
                config.update_tag,
                common_job_parameters,
            )
            if workspace["sync_public_pages"]:
                pages.sync(
                    neo4j_session,
                    api_session,
                    workspace["id"],
                    config.update_tag,
                )
            logger.info("Completed Notion workspace sync")
    finally:
        for api_session in api_sessions:
            api_session.close()
