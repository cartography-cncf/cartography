import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import cartography.intel.netlify.accounts
import cartography.intel.netlify.agentrunners
import cartography.intel.netlify.buildhooks
import cartography.intel.netlify.certificates
import cartography.intel.netlify.databases
import cartography.intel.netlify.deploykeys
import cartography.intel.netlify.deploys
import cartography.intel.netlify.devservers
import cartography.intel.netlify.dns
import cartography.intel.netlify.envvars
import cartography.intel.netlify.forms
import cartography.intel.netlify.functions
import cartography.intel.netlify.hooks
import cartography.intel.netlify.serviceinstances
import cartography.intel.netlify.sites
import cartography.intel.netlify.snippets
import cartography.intel.netlify.users
from cartography.config import Config
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# The CLI supplies this too, but Config defaults it to None, so a caller building a Config
# programmatically would otherwise request "None/accounts".
DEFAULT_BASE_URL = "https://api.netlify.com/api/v1"


def _build_api_session(token: str) -> requests.Session:
    """
    Build the authenticated session every get_* function shares.

    Netlify allows 500 requests per minute and answers a breach with 429 plus a `Retry-After`
    header, which urllib3's Retry honours, so rate limiting needs no handling of its own.
    """
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {token}"})
    return api_session


@timeit
def start_netlify_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Netlify data. Otherwise warn and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.netlify_token or not config.netlify_account_slug:
        logger.info(
            "Netlify import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = _build_api_session(config.netlify_token)
    # Resolved once here so the account lookup and every domain sync share the same value.
    base_url = config.netlify_base_url or DEFAULT_BASE_URL
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": config.update_tag,
    }

    account = cartography.intel.netlify.accounts.sync_netlify_account(
        neo4j_session,
        api_session,
        base_url,
        config.netlify_account_slug,
        config.update_tag,
    )
    account_id = account["id"]

    # Every scoped cleanup job resolves its tenant from this key, so it has to be set before any
    # domain sync runs and removed afterwards so a later module cannot inherit it.
    common_job_parameters["NETLIFY_ACCOUNT_ID"] = account_id
    try:
        _sync_one_account(
            neo4j_session,
            api_session,
            base_url,
            account_id,
            config.netlify_account_slug,
            config.update_tag,
            common_job_parameters,
        )
    finally:
        common_job_parameters.pop("NETLIFY_ACCOUNT_ID", None)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="NetlifyAccount",
        group_id=account_id,
        synced_type="NetlifyAccount",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )


@timeit
def _sync_one_account(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    account_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync every resource of one Netlify team.

    Ordering matters in three ways.

    Users come first, because deploys, env vars and agent runners all point at them.

    The site list is fetched next but loaded later. Deploy keys have to be loaded before the sites
    are: a site's `USES_DEPLOY_KEY` edge is resolved by a MATCH when the site row is written, so a
    key node that does not exist yet yields no edge at all until the following sync. The deploy key
    sync also needs the site list to decide which of the token's keys belong to this team.

    Every remaining domain is scoped to a site and iterates the same list.

    Each domain sync loops over the full site list internally and then runs its cleanup once.
    Running cleanup inside the site loop would delete the not-yet-visited sites' nodes from the
    previous run and recreate them later in the same loop, which is a hole for concurrent readers
    and permanent data loss if a later request fails.
    """
    cartography.intel.netlify.users.sync_netlify_users(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        account_slug,
        update_tag,
        common_job_parameters,
    )
    sites = cartography.intel.netlify.sites.get_netlify_sites(
        api_session,
        base_url,
        account_slug,
    )
    cartography.intel.netlify.deploykeys.sync_netlify_deploy_keys(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.sites.sync_netlify_sites(
        neo4j_session,
        sites,
        account_id,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.deploys.sync_netlify_deploys(
        neo4j_session,
        sites,
        account_id,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.functions.sync_netlify_functions(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.devservers.sync_netlify_dev_servers(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.agentrunners.sync_netlify_agent_runners(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.databases.sync_netlify_databases(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.envvars.sync_netlify_env_vars(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.buildhooks.sync_netlify_build_hooks(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.hooks.sync_netlify_hooks(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.snippets.sync_netlify_snippets(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.serviceinstances.sync_netlify_service_instances(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.certificates.sync_netlify_certificates(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.forms.sync_netlify_forms(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        sites,
        update_tag,
        common_job_parameters,
    )
    cartography.intel.netlify.dns.sync_netlify_dns(
        neo4j_session,
        api_session,
        base_url,
        account_id,
        account_slug,
        update_tag,
        common_job_parameters,
    )
