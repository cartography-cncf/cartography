import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.railway.deployments
import cartography.intel.railway.environments
import cartography.intel.railway.iam.tokens
import cartography.intel.railway.iam.users
import cartography.intel.railway.network.domains
import cartography.intel.railway.network.tcpproxies
import cartography.intel.railway.projects
import cartography.intel.railway.serviceinstances
import cartography.intel.railway.services
import cartography.intel.railway.storage.volumes
import cartography.intel.railway.variables
from cartography.config import Config
from cartography.intel.railway.queries import ME_QUERY
from cartography.intel.railway.utils import call_railway_api
from cartography.intel.railway.utils import RailwayGraphQLError
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://backboard.railway.com/graphql/v2"


def _build_api_session(token: str) -> requests.Session:
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        # 429 is deliberately absent: urllib3 honours Retry-After itself, so it would sleep
        # inside the adapter before call_railway_api() ever sees the response, bypassing the
        # _MAX_RETRY_AFTER_SECONDS cap and potentially stalling a sync for the better part of
        # an hour. Rate limiting is handled by the explicit retry loop there instead.
        status_forcelist=[500, 502, 503, 504],
        # Railway's API is GraphQL over POST, so POST must be retryable. Leaving the urllib3
        # default of idempotent-methods-only would silently disable retries entirely.
        allowed_methods=["POST"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {token}"})
    return api_session


@timeit
def get_account(
    api_session: requests.Session,
    base_url: str,
) -> dict[str, Any] | None:
    """
    Identify the token holder and the workspaces it can reach.

    Only account-scoped tokens can read `me`; a workspace-scoped token gets
    `Not Authorized` back. That is not fatal as long as the operator pinned a workspace id,
    so this returns None rather than raising.
    """
    try:
        data = call_railway_api(api_session, base_url, ME_QUERY)
    except RailwayGraphQLError as err:
        if not err.is_not_authorized:
            raise
        logger.info(
            "Railway token is not authorized to read the account profile; "
            "continuing with the configured workspace only.",
        )
        return None
    return data["me"]


@timeit
def start_railway_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Railway data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.railway_token:
        logger.info(
            "Railway import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = _build_api_session(config.railway_token)
    base_url = config.railway_base_url or DEFAULT_BASE_URL

    account = get_account(api_session, base_url)
    account_user_id = account["id"] if account else None

    if config.railway_workspace_id:
        workspace_ids = [config.railway_workspace_id]
    elif account:
        # Railway rejects `projects` queries that omit a workspaceId, so a workspace is the
        # mandatory root of every sync.
        workspace_ids = [workspace["id"] for workspace in account["workspaces"]]
    else:
        logger.warning(
            "Railway token cannot enumerate workspaces and no --railway-workspace-id was "
            "given - skipping this module.",
        )
        return

    if not workspace_ids:
        logger.warning("Railway token has access to no workspaces - nothing to sync.")
        return

    for workspace_id in workspace_ids:
        logger.info("Syncing Railway workspace %s", workspace_id)
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "BASE_URL": base_url,
            "WORKSPACE_ID": workspace_id,
        }
        _sync_workspace(
            neo4j_session,
            api_session,
            common_job_parameters,
            account_user_id,
            config.update_tag,
        )


def _sync_workspace(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    account_user_id: str | None,
    update_tag: int,
) -> None:
    # Ordering matters so that cross-resource matchers resolve: the workspace tenant and its
    # projects first, then the principals that tokens are owned by, then everything scoped
    # to a project.
    workspace, projects = cartography.intel.railway.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        update_tag,
    )
    cartography.intel.railway.iam.users.sync(
        neo4j_session,
        common_job_parameters,
        workspace,
        projects,
        update_tag,
    )
    # Tokens after users so the OWNED_BY edge has a principal to attach to.
    cartography.intel.railway.iam.tokens.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        projects,
        account_user_id,
        update_tag,
    )

    # One request per project pulls everything below it; the domain syncs below then work
    # off these bundles without touching the network again.
    bundles = {
        project["id"]: cartography.intel.railway.projects.get_project_bundle(
            api_session,
            common_job_parameters["BASE_URL"],
            project["id"],
        )
        for project in projects
    }

    cartography.intel.railway.environments.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )
    cartography.intel.railway.services.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )
    # TCP proxies are a separate root field, so they are fetched before the service instance
    # sync (which needs them to decide is_publicly_exposed) but loaded after it (their
    # EXPOSE edges need the instance nodes to exist).
    tcp_proxies_by_project, tcp_proxies_by_instance = (
        cartography.intel.railway.network.tcpproxies.get_all(
            api_session,
            common_job_parameters["BASE_URL"],
            bundles,
        )
    )

    # Service instances need environments and services to exist first so their HAS edges
    # resolve.
    cartography.intel.railway.serviceinstances.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        tcp_proxies_by_instance,
        workspace,
        update_tag,
    )
    cartography.intel.railway.network.domains.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )
    cartography.intel.railway.network.tcpproxies.sync(
        neo4j_session,
        common_job_parameters,
        tcp_proxies_by_project,
        update_tag,
    )
    # The remaining resources all attach to service instances, so they follow it.
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )
    cartography.intel.railway.storage.volumes.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )
    cartography.intel.railway.variables.sync(
        neo4j_session,
        common_job_parameters,
        bundles,
        update_tag,
    )

    # DEPRECATED: compatibility migration that drops the legacy
    # (:RailwayServiceInstance)-[:EXPOSE]->(domain) edges left by the direction flip.
    # Generated cleanup only matches the new orientation, so without this a graph upgraded
    # in place would hold both. Scoped to instances this run refreshed, so a workspace this
    # run never touched keeps its edges until its own sync. Remove in v1.0.0.
    run_analysis_job(
        "railway_expose_edge_direction_migration.json",
        neo4j_session,
        common_job_parameters,
    )
