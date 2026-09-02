import logging

import neo4j
import requests

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

    try:
        cartography.intel.runpod.sshkeys.sync(**sync_kwargs)
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "RunPod SSH keys sync failed - skipping this resource type and its "
            "cleanup for this run, continuing with the rest of the account sync: %s",
            exc,
        )

    try:
        cartography.intel.runpod.registries.sync(**sync_kwargs)
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "RunPod registry credentials sync failed - skipping this resource type "
            "and its cleanup for this run, continuing with the rest of the account "
            "sync: %s",
            exc,
        )

    try:
        cartography.intel.runpod.catalog.sync(**sync_kwargs)
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "RunPod data centers sync failed - skipping this resource type and its "
            "cleanup for this run, continuing with the rest of the account sync: %s",
            exc,
        )

    cartography.intel.runpod.network_volumes.sync(**sync_kwargs)
    cartography.intel.runpod.templates.sync(**sync_kwargs)
    cartography.intel.runpod.pods.sync(**sync_kwargs)
    cartography.intel.runpod.serverless.sync(**sync_kwargs)
    cartography.intel.runpod.clusters.sync(**sync_kwargs)
