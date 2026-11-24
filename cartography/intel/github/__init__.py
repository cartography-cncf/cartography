import base64
import json
import logging
from typing import Any
from typing import cast

import neo4j

import cartography.intel.github.actions
import cartography.intel.github.app_installations
import cartography.intel.github.codeowners
import cartography.intel.github.commits
import cartography.intel.github.container_image_attestations
import cartography.intel.github.container_image_tags
import cartography.intel.github.container_images
import cartography.intel.github.dependabot_alerts
import cartography.intel.github.external_identities
import cartography.intel.github.organizations
import cartography.intel.github.packages
import cartography.intel.github.personal_access_tokens
import cartography.intel.github.repos
import cartography.intel.github.supply_chain
import cartography.intel.github.teams
import cartography.intel.github.users
import cartography.intel.github.webhooks
import cartography.intel.supply_chain
from cartography.client.core.tx import read_list_of_values_tx
from cartography.config import Config
from cartography.intel.github.app_auth import make_credential
from cartography.intel.github.util import github_org_url
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_repos_from_graph(neo4j_session: neo4j.Session, org_url: str) -> list[str]:
    """
    Get repository names for an organization from the graph instead of making an API call.

    :param neo4j_session: Neo4j session for database interface
    :param org_url: The organization URL, as GitHub reports it
    :return: List of repository names
    """
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
    cartography.intel.github.personal_access_tokens.cleanup_orphaned_classic_personal_access_tokens(
        neo4j_session,
        common_job_parameters,
    )
    cartography.intel.github.repos.cleanup_global_resources(
        neo4j_session,
        common_job_parameters,
    )

    # DEPRECATED: one-time orphaned branch migration will be removed in v1.0.0.
    cartography.intel.github.repos.cleanup_orphaned_github_branches(
        neo4j_session,
        common_job_parameters,
    )


@timeit
@timeit
def sync_ghcr(
    neo4j_session: neo4j.Session,
    token: Any,
    api_url: str,
    organization: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> bool:
    """
    Sync one organization's GitHub Container Registry: container packages,
    image manifests and layers, tags, and SLSA attestations. Returns whether
    GitHub listed the organization's packages; False means it refused the
    token or the endpoint, nothing was synced, and nothing was cleaned up.

    :param token: A classic PAT with ``read:packages``. GitHub Packages and
        ghcr.io refuse GitHub App installation tokens and fine-grained PATs,
        so an orchestrator that authenticates the organization with either
        runs this with a separate token, or skips it with ``skip_ghcr``.

    Everything after the package list is gated on ``cleanup_safe``, not on the
    list being non-empty, so an organization that legitimately has zero
    packages still gets its stale images, tags, and attestations reaped, while
    an endpoint outage or a refused token disables both the fetches and the
    downstream cleanups and leaves previously synced nodes alone.
    """
    ghcr_result = cartography.intel.github.packages.sync_packages(
        neo4j_session,
        token,
        api_url,
        organization,
        update_tag,
        common_job_parameters,
    )
    if not ghcr_result.cleanup_safe:
        return False
    (
        ghcr_manifests,
        _ghcr_manifest_lists,
        ghcr_tag_rows,
        ghcr_observed_and_skipped,
    ) = cartography.intel.github.container_images.sync_container_images(
        neo4j_session,
        token,
        api_url,
        organization,
        ghcr_result.packages,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.github.container_image_tags.sync_container_image_tags(
        neo4j_session,
        organization,
        ghcr_tag_rows,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.github.container_image_attestations.sync_container_image_attestations(
        neo4j_session,
        token,
        api_url,
        organization,
        ghcr_manifests,
        update_tag,
        common_job_parameters,
        additional_observed_digests=ghcr_observed_and_skipped,
    )
    return True


def start_github_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
    *,
    skip_unscoped_cleanup: bool = False,
    skip_ghcr: bool = False,
) -> None:
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :param skip_unscoped_cleanup: Skip cleanup of GitHub resources that are not
        scoped to a single organization. External orchestrators that set this
        to True should call cleanup_unscoped_github_resources() once after all
        organizations have been refreshed with the same update tag.
    :param skip_ghcr: Skip the GitHub Container Registry for every
        organization. GitHub Packages accepts only classic PATs with
        ``read:packages``, so an orchestrator that authenticates organizations
        with a GitHub App or a fine-grained PAT sets this and runs sync_ghcr()
        itself with a classic PAT; previously synced GHCR nodes are left alone.
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
    cartography.intel.supply_chain.migrate_source_folder_urls(
        neo4j_session,
        common_job_parameters,
    )

    # run sync for the provided github organizations
    for auth_data in auth_tokens["organization"]:
        credential = make_credential(auth_data)
        api_url = auth_data["url"]
        org_name = auth_data["name"]

        # credential is a GitHubCredential (duck-typed as str by _resolve_token in util.py)
        token: Any = credential

        user_data, owners_data, org_data = (
            cartography.intel.github.users.get_organization(token, api_url, org_name)
        )
        # Writes the GitHubOrganization node; every later sync attaches to it.
        cartography.intel.github.organizations.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
            org_data,
        )
        github_users = cartography.intel.github.users.sync(
            neo4j_session,
            common_job_parameters,
            user_data,
            owners_data,
            org_data,
        )
        cartography.intel.github.external_identities.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        repo_sync_result = cartography.intel.github.repos.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.personal_access_tokens.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.app_installations.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.webhooks.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
            repo_sync_result.repos,
            repos_complete=repo_sync_result.repos_complete,
        )
        cartography.intel.github.dependabot_alerts.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        github_teams = cartography.intel.github.teams.sync_github_teams(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
        )
        cartography.intel.github.codeowners.sync(
            neo4j_session,
            common_job_parameters,
            token,
            api_url,
            org_name,
            repo_sync_result.repos,
            repo_sync_result.manifests,
            dependency_manifests_cleanup_safe=repo_sync_result.manifests_cleanup_safe,
            github_users=github_users,
            github_teams=github_teams,
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
        repo_names = _get_repos_from_graph(
            neo4j_session, github_org_url(api_url, org_name)
        )

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

        # Runs before supply_chain.sync so the latter can correlate digests.
        if not skip_ghcr:
            sync_ghcr(
                neo4j_session,
                token,
                api_url,
                org_name,
                common_job_parameters["UPDATE_TAG"],
                common_job_parameters,
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
