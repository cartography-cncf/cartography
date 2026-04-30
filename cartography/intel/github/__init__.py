import base64
import json
import logging
from typing import Any
from typing import cast

import neo4j

import cartography.intel.github.actions
import cartography.intel.github.commits
import cartography.intel.github.container_image_attestations
import cartography.intel.github.container_image_tags
import cartography.intel.github.container_images
import cartography.intel.github.packages
import cartography.intel.github.repos
import cartography.intel.github.supply_chain
import cartography.intel.github.teams
import cartography.intel.github.users
from cartography.client.core.tx import read_list_of_values_tx
from cartography.config import Config
from cartography.intel.github.app_auth import make_credential
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
def cleanup_unscoped_github_resources(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up GitHub resources that are not scoped to a single organization.

    External orchestrators that call start_github_ingestion() with
    skip_unscoped_cleanup=True should call this once after all organizations
    have been refreshed with the same update tag.
    """
    cartography.intel.github.users.cleanup(neo4j_session, common_job_parameters)
    cartography.intel.github.repos.cleanup_global_resources(
        neo4j_session,
        common_job_parameters,
    )

    # DEPRECATED: one-time migration, run once per sync cycle (not per org)
    cartography.intel.github.repos.cleanup_orphaned_github_branches(
        neo4j_session,
        common_job_parameters,
    )


@timeit
def start_github_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
    *,
    skip_unscoped_cleanup: bool = False,
) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :param skip_unscoped_cleanup: Skip cleanup of GitHub resources that are not
        scoped to a single organization. External orchestrators that set this
        to True should call cleanup_unscoped_github_resources() once after all
        organizations have been refreshed with the same update tag.
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
    processed_any_org = False

    # run sync for the provided github organizations
    for auth_data in auth_tokens["organization"]:
        credential = make_credential(auth_data)
        api_url = auth_data["url"]
        org_name = auth_data["name"]

        # credential is a GitHubCredential (duck-typed as str by _resolve_token in util.py)
        token: Any = credential

        cartography.intel.github.users.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.repos.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.teams.sync_github_teams(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )

        # Sync GitHub Actions (workflows, secrets, variables, environments)
        all_workflows = cartography.intel.github.actions.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )

        # Sync commit relationships for the configured lookback period
        # Get repo names from the graph instead of making another API call
        repo_names = _get_repos_from_graph(neo4j_session, org_name)

        cartography.intel.github.commits.sync_github_commits(
            neo4j_session,
            token,
            api_url,
            org_name,
            repo_names,
            common_job_parameters["UPDATE_TAG"],
            config.github_commit_lookback_days,
        )

        repos_json = cartography.intel.github.repos.get(
            token,
            api_url,
            org_name,
        )
        # Filter out None entries
        valid_repos = [r for r in repos_json if r is not None]

        # Sync GHCR (container packages, image manifests, tags, attestations).
        # Runs before supply_chain.sync so the latter can correlate digests.
        # Gate on cleanup_safe — not on the packages list — so an org that
        # legitimately has zero packages still gets its stale GHCR images,
        # tags, and attestations reaped. An endpoint outage or missing-scope
        # condition flips cleanup_safe to False, which disables both the
        # fetches and the downstream cleanups.
        ghcr_result = cartography.intel.github.packages.sync_packages(
            neo4j_session,
            token,
            api_url,
            org_name,
            common_job_parameters["UPDATE_TAG"],
            common_job_parameters,
        )
        if ghcr_result.cleanup_safe:
            (
                ghcr_manifests,
                _ghcr_manifest_lists,
                ghcr_tag_rows,
                ghcr_observed_and_skipped,
            ) = cartography.intel.github.container_images.sync_container_images(
                neo4j_session,
                token,
                api_url,
                org_name,
                ghcr_result.packages,
                common_job_parameters["UPDATE_TAG"],
                common_job_parameters,
            )
            cartography.intel.github.container_image_tags.sync_container_image_tags(
                neo4j_session,
                org_name,
                ghcr_tag_rows,
                common_job_parameters["UPDATE_TAG"],
                common_job_parameters,
            )
            cartography.intel.github.container_image_attestations.sync_container_image_attestations(
                neo4j_session,
                token,
                api_url,
                org_name,
                ghcr_manifests,
                common_job_parameters["UPDATE_TAG"],
                common_job_parameters,
                additional_observed_digests=ghcr_observed_and_skipped,
            )

        if valid_repos:
            cartography.intel.github.supply_chain.sync(
                neo4j_session,
                token,
                api_url,
                org_name,
                common_job_parameters["UPDATE_TAG"],
                common_job_parameters,
                valid_repos,
                workflows=all_workflows,
            )

        processed_any_org = True

    if processed_any_org and not skip_unscoped_cleanup:
        cleanup_unscoped_github_resources(
            neo4j_session,
            common_job_parameters,
        )
