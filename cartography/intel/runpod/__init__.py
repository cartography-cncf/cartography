import logging

import neo4j

import cartography.intel.runpod.account
import cartography.intel.runpod.catalog
import cartography.intel.runpod.clusters
import cartography.intel.runpod.network_volumes
import cartography.intel.runpod.pods
import cartography.intel.runpod.registries
import cartography.intel.runpod.serverless
import cartography.intel.runpod.sshkeys
import cartography.intel.runpod.templates
from cartography.config import Config
from cartography.intel.runpod.util import BASE_URL
from cartography.intel.runpod.util import build_session
from cartography.intel.runpod.util import safe_sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_runpod_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of RunPod inventory. Otherwise skip.
    """
    if not config.runpod_api_key or not config.runpod_account_id:
        logger.info(
            "RunPod import is not configured - skipping this module. Set "
            "runpod_api_key and runpod_account_id to enable the RunPod sync stage.",
        )
        return

    session = build_session(config.runpod_api_key)
    base_url = config.runpod_base_url or BASE_URL
    account_id = config.runpod_account_id
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "RUNPOD_ACCOUNT_ID": account_id,
    }

    cartography.intel.runpod.account.sync(
        neo4j_session,
        account_id,
        config.update_tag,
    )

    sync_kwargs = {
        "neo4j_session": neo4j_session,
        "session": session,
        "base_url": base_url,
        "account_id": account_id,
        "update_tag": config.update_tag,
        "common_job_parameters": common_job_parameters,
    }

    safe_sync(
        "SSH keys",
        cartography.intel.runpod.sshkeys.sync,
        required=False,
        **sync_kwargs,
    )
    safe_sync(
        "registry credentials",
        cartography.intel.runpod.registries.sync,
        required=False,
        **sync_kwargs,
    )
    safe_sync(
        "data centers",
        cartography.intel.runpod.catalog.sync,
        required=False,
        **sync_kwargs,
    )
    safe_sync(
        "network volumes",
        cartography.intel.runpod.network_volumes.sync,
        required=True,
        **sync_kwargs,
    )
    safe_sync(
        "templates",
        cartography.intel.runpod.templates.sync,
        required=True,
        **sync_kwargs,
    )
    safe_sync("pods", cartography.intel.runpod.pods.sync, required=True, **sync_kwargs)
    safe_sync(
        "serverless endpoints",
        cartography.intel.runpod.serverless.sync,
        required=True,
        **sync_kwargs,
    )
    safe_sync(
        "clusters",
        cartography.intel.runpod.clusters.sync,
        required=True,
        **sync_kwargs,
    )
