"""
Proxmox Virtual Environment intelligence module for Cartography.

This module syncs Proxmox infrastructure including clusters, nodes, VMs,
containers, storage, networks, users, and backup configurations.
"""

import logging
import os
from typing import Any, Dict

from cartography.config import Config
from cartography.intel.proxmox import cluster
from cartography.intel.proxmox import compute
from cartography.intel.proxmox import storage
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_proxmox_client(config: Config):
    """
    Create and return a Proxmox API client.

    :param config: Cartography configuration object
    :return: ProxmoxAPI client
    :raises: ValueError if credentials not found in environment or proxmoxer not installed
    """
    try:
        from proxmoxer import ProxmoxAPI
    except ImportError:
        raise ImportError(
            "The proxmoxer library is required for Proxmox sync. "
            "Install it with: pip install proxmoxer"
        )

    host = config.proxmox_host
    port = config.proxmox_port
    user = config.proxmox_user
    verify_ssl = config.proxmox_verify_ssl

    # Try token-based auth first (recommended)
    if config.proxmox_token_name_env_var and config.proxmox_token_value_env_var:
        token_name = os.environ.get(config.proxmox_token_name_env_var)
        token_value = os.environ.get(config.proxmox_token_value_env_var)

        if not token_name:
            raise ValueError(
                f"Environment variable {config.proxmox_token_name_env_var} "
                f"not found or is empty"
            )
        if not token_value:
            raise ValueError(
                f"Environment variable {config.proxmox_token_value_env_var} "
                f"not found or is empty"
            )

        logger.info(f"Connecting to Proxmox at {host} using API token")
        return ProxmoxAPI(
            host,
            port=port,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
        )

    # Fall back to password auth
    elif config.proxmox_password_env_var:
        password = os.environ.get(config.proxmox_password_env_var)

        if not password:
            raise ValueError(
                f"Environment variable {config.proxmox_password_env_var} "
                f"not found or is empty"
            )

        logger.info(f"Connecting to Proxmox at {host} using password auth")
        return ProxmoxAPI(
            host,
            port=port,
            user=user,
            password=password,
            verify_ssl=verify_ssl,
        )

    else:
        raise ValueError("No Proxmox authentication method configured")


@timeit
def start_proxmox_ingestion(neo4j_session, config: Config) -> None:
    """
    Main entry point for Proxmox data ingestion.

    This is the primary sync function called by Cartography's sync orchestrator.

    :param neo4j_session: Neo4j session for database operations
    :param config: Cartography configuration object
    """
    if not config.proxmox_host:
        logger.info("Proxmox host not configured, skipping Proxmox sync")
        return

    logger.info(f"Starting Proxmox infrastructure sync for {config.proxmox_host}")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    try:
        # Get Proxmox API client
        proxmox_client = _get_proxmox_client(config)

        # Sync cluster and nodes (returns cluster_id for other modules)
        cluster_data = cluster.sync(
            neo4j_session,
            proxmox_client,
            config.proxmox_host,
            config.update_tag,
            common_job_parameters,
        )

        cluster_id = cluster_data['cluster_id']

        # Sync VMs and containers
        compute.sync(
            neo4j_session,
            proxmox_client,
            cluster_id,
            config.update_tag,
            common_job_parameters,
        )

        # Sync storage
        storage.sync(
            neo4j_session,
            proxmox_client,
            cluster_id,
            config.update_tag,
            common_job_parameters,
        )

        # Run cleanup to remove stale data
        run_cleanup_job(
            'proxmox_import_cleanup.json',
            neo4j_session,
            common_job_parameters,
        )

        merge_module_sync_metadata(
            neo4j_session,
            group_type='ProxmoxCluster',
            group_id=cluster_id,
            synced_type='ProxmoxCluster',
            update_tag=config.update_tag,
            stat_handler=None,
        )

        logger.info("Completed Proxmox infrastructure sync")

    except Exception as e:
        logger.error(f"Error syncing Proxmox cluster {config.proxmox_host}: {e}", exc_info=True)
        raise
