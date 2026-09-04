import logging
from typing import Any

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import
from cartography.util.lazy import lazy_namespace_all
from cartography.util.lazy import lazy_submodule

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
Cloudflare = lazy_callable("cloudflare", "Cloudflare")
_dnsrecords = lazy_import("cartography.intel.cloudflare.dnsrecords")
sync_accounts = lazy_callable("cartography.intel.cloudflare.accounts", "sync")
sync_members = lazy_callable("cartography.intel.cloudflare.members", "sync")
sync_r2buckets = lazy_callable("cartography.intel.cloudflare.r2buckets", "sync")
sync_roles = lazy_callable("cartography.intel.cloudflare.roles", "sync")
sync_rulesets = lazy_callable("cartography.intel.cloudflare.rulesets", "sync")
sync_workerroutes = lazy_callable("cartography.intel.cloudflare.workerroutes", "sync")
sync_workerscripts = lazy_callable("cartography.intel.cloudflare.workerscripts", "sync")
sync_zones = lazy_callable("cartography.intel.cloudflare.zones", "sync")

logger = logging.getLogger(__name__)


@timeit
def start_cloudflare_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Cloudflare data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.cloudflare_token:
        message = (
            "Cloudflare import is not configured - missing cloudflare_token. "
            "Set the token to enable the Cloudflare sync stage."
        )
        logger.error(message)
        raise RuntimeError(message)

    # Create client
    client = Cloudflare(api_token=config.cloudflare_token)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    for account in sync_accounts(
        neo4j_session,
        client,
        common_job_parameters,
    ):
        account_job_parameters = common_job_parameters.copy()
        account_job_parameters["account_id"] = account["id"]
        sync_roles(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        sync_members(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        # Runs before the zone sync: zone cleanup deletes stale zones, which
        # would orphan the DNS records only reachable through them.
        _dnsrecords.migrate_account_resource_edges(
            neo4j_session,
            account_job_parameters,
        )

        zones = sync_zones(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        _dnsrecords.sync(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
            zones=zones,
        )

        sync_r2buckets(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        # Runs before the route sync, which links each route to the script it
        # invokes.
        sync_workerscripts(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        sync_workerroutes(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
            zones=zones,
        )

        sync_rulesets(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
            zones=zones,
        )


# DEPRECATED: importing this package used to populate its namespace with every
# submodule the entry point pulled, so callers could reach a stage through
# `cartography.intel.cloudflare.<domain>`. Those imports are lazy now, so the names are served on
# demand instead. Remove in v1.0.0.
def __getattr__(name: str) -> Any:
    return lazy_submodule(__name__, name)


# A star-import only reaches __getattr__ for names __all__ mentions, so the shim above
# needs this to cover `from cartography.intel.cloudflare import *` too.
__all__ = lazy_namespace_all(__path__, globals())
