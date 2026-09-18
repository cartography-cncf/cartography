import logging
from typing import Any

import neo4j

import cartography.intel.bitbucket.projects
import cartography.intel.bitbucket.repositories
import cartography.intel.bitbucket.users
import cartography.intel.bitbucket.workspaces
from cartography.config import Config
from cartography.intel.bitbucket.auth import make_credential
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _is_configured(config: Config) -> bool:
    if not config.bitbucket_workspaces:
        return False
    if config.bitbucket_auth_method == "oauth":
        return bool(
            config.bitbucket_oauth_client_id
            and config.bitbucket_oauth_client_secret
            and config.bitbucket_oauth_refresh_token
        )
    return bool(config.bitbucket_token)


@timeit
def start_bitbucket_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Bitbucket Cloud data.
    Otherwise warn and exit.
    """
    if not _is_configured(config):
        logger.info(
            "Bitbucket import is not configured - skipping this module. "
            "See docs to configure (requires --bitbucket-workspaces and either "
            "--bitbucket-token-env-var or the --bitbucket-oauth-* flags).",
        )
        return

    credential = make_credential(
        config.bitbucket_auth_method or "token",
        config.bitbucket_token,
        config.bitbucket_oauth_client_id,
        config.bitbucket_oauth_client_secret,
        config.bitbucket_oauth_refresh_token,
    )

    configured_slugs = [slug.strip() for slug in config.bitbucket_workspaces.split(",")]

    common_job_parameters: dict[str, Any] = {"UPDATE_TAG": config.update_tag}

    logger.info("Starting Bitbucket Cloud sync")

    all_workspaces = cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces(
        neo4j_session,
        credential,
        config.update_tag,
        configured_slugs,
    )

    cartography.intel.bitbucket.projects.sync_bitbucket_projects(
        neo4j_session,
        credential,
        config.update_tag,
        all_workspaces,
    )

    cartography.intel.bitbucket.repositories.sync_bitbucket_repositories(
        neo4j_session,
        credential,
        config.update_tag,
        all_workspaces,
    )

    users_skipped = cartography.intel.bitbucket.users.sync_bitbucket_users(
        neo4j_session,
        credential,
        config.update_tag,
        all_workspaces,
    )

    # Cleanup in reverse order (leaf to root) so a workspace's children are
    # gone before the workspace node itself is considered for removal.
    logger.info("Starting Bitbucket cleanup phase")
    for workspace in all_workspaces:
        cartography.intel.bitbucket.repositories.cleanup_repositories(
            neo4j_session, common_job_parameters, workspace["id"]
        )
        if workspace["id"] not in users_skipped:
            cartography.intel.bitbucket.users.cleanup_users(
                neo4j_session, common_job_parameters, workspace["id"]
            )
        cartography.intel.bitbucket.projects.cleanup_projects(
            neo4j_session, common_job_parameters, workspace["id"]
        )

    cartography.intel.bitbucket.workspaces.cleanup_workspaces(
        neo4j_session, common_job_parameters
    )

    logger.info("Completed Bitbucket Cloud sync")
