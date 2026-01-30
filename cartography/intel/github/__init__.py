import base64
import json
import logging
from typing import cast

import neo4j

import cartography.intel.github.commits
import cartography.intel.github.repos
import cartography.intel.github.teams
import cartography.intel.github.users
from cartography.client.core.tx import read_list_of_values_tx
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_repos_from_graph(neo4j_session: neo4j.Session, organization: str) -> list[str]:
    """
    Get repository names for an organization from the graph instead of making an API call.

    :param neo4j_session: Neo4j session for database interface
    :param organization: GitHub organization name
    :return: List of repository names
    """
    org_url = f"https://github.com/{organization}"
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})<-[:OWNER]-(repo:GitHubRepository)
    RETURN repo.name
    ORDER BY repo.name
    """
    return cast(
        list[str],
        neo4j_session.execute_read(
            read_list_of_values_tx,
            query,
            org_url=org_url,
        ),
    )


@timeit
def start_github_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.github_config:
        logger.info(
            "GitHub import is not configured - skipping this module. See docs to configure.",
        )
        return

    auth_tokens = json.loads(base64.b64decode(config.github_config).decode())
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    # run sync for the provided github tokens
    for auth_data in auth_tokens["organization"]:
        cartography.intel.github.users.sync(
            neo4j_session,
            common_job_parameters,
            auth_data["token"],
            auth_data["url"],
            auth_data["name"],
        )
        cartography.intel.github.repos.sync(
            neo4j_session,
            common_job_parameters,
            auth_data["token"],
            auth_data["url"],
            auth_data["name"],
        )
        cartography.intel.github.teams.sync_github_teams(
            neo4j_session,
            common_job_parameters,
            auth_data["token"],
            auth_data["url"],
            auth_data["name"],
        )

        # Sync commit relationships for the configured lookback period
        # Get repo names from the graph instead of making another API call
        repo_names = _get_repos_from_graph(neo4j_session, auth_data["name"])

        cartography.intel.github.commits.sync_github_commits(
            neo4j_session,
            auth_data["token"],
            auth_data["url"],
            auth_data["name"],
            repo_names,
            common_job_parameters["UPDATE_TAG"],
            config.github_commit_lookback_days,
        )
