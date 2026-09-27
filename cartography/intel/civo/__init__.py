import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.civo.account
import cartography.intel.civo.sshkeys
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.civo.com"


@timeit
def start_civo_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Civo data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.civo_api_key:
        logger.info(
            "Civo import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"bearer {config.civo_api_key}"})
    base_url = config.civo_base_url or DEFAULT_BASE_URL

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": base_url,
    }

    # Phase 1: Root tenant
    account = cartography.intel.civo.account.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    common_job_parameters["ACCOUNT_ID"] = account["id"]

    # Phase 2: Account-scoped resources. Each follow-up Civo resource PR adds
    # its own sync() call here, after this foundation PR merges. Neither of
    # this foundation PR's own resources (CivoAccount, CivoSSHKey) is
    # region-scoped, so REGIONS is deliberately not fetched here - a
    # regional resource's own PR is responsible for populating
    # common_job_parameters["REGIONS"] (via the shared get_regions() helper
    # in cartography.intel.civo.util) immediately before its own sync()
    # call, guarded by `if "REGIONS" not in common_job_parameters` so it's
    # fetched at most once regardless of merge order among regional PRs.
    # This keeps a malformed/unavailable /v2/regions response from blocking
    # ingestion of resources that never needed it in the first place (e.g.
    # CivoAccount, CivoSSHKey, CivoDNSDomain/Record, CivoTeam/Role/
    # Permission - none of Civo's account, ssh key, DNS, or IAM endpoints
    # are region-scoped).
    cartography.intel.civo.sshkeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Phase 3: cleanup, only after every fetch/transform/load above has
    # succeeded, in the reverse of the load order (most-dependent resources
    # first, root tenant last). Interleaving cleanup with loading (as this
    # module used to do) means an exception partway through phase 2 leaves
    # the graph in a mixed state: everything cleaned up so far reflects a
    # fresh snapshot, while resources not yet reached this run keep stale
    # data - and, worse, any node deleted by an earlier cleanup severs the
    # relationship edges other not-yet-reloaded nodes still hold to it, even
    # though those nodes themselves were never touched. Deferring every
    # cleanup to the end means a mid-sync failure aborts before any cleanup
    # runs at all - earlier loads in this same run have already committed
    # (a partial sync can still add/update nodes), but no stale node from a
    # *previous* run is deleted until every load in *this* run has
    # succeeded, instead of some stale nodes being pruned while others -
    # and the edges severed by that pruning - are left inconsistent.
    cartography.intel.civo.sshkeys.cleanup(neo4j_session, common_job_parameters)
    # CivoAccountSchema has no relationships of its own (it's the root
    # tenant), so its cleanup() is a no-op today - same as every other
    # tenant-root schema in this codebase with no sub_resource_relationship
    # (AWSAccount, DigitalOceanAccount, CloudflareAccount, ...). Called here
    # anyway for forward-compatibility if that ever changes, and to keep
    # this phase's ordering visibly complete.
    cartography.intel.civo.account.cleanup(neo4j_session, common_job_parameters)
