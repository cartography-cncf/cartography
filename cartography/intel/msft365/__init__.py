# cartography/intel/msft365/__init__.py
"""
Msft365 integration module for Cartography.
This module synchronizes users, groups, and organizational units from Microsoft 365
into the Cartography graph database.
"""

import logging
from typing import Dict, List, Any, Optional

# Import functions from msft365.py 
from cartography.intel.msft365.msft365 import (
    sync_Msft365_users,
    sync_Msft365_groups,
    sync_Msft365_organizational_units,
    sync_Msft365_devices,
    sync_Msft365_user_group_relationships,
    sync_Msft365_ou_relationships,
    sync_Msft365_device_relationships,

    get_access_token,
    run_cleanup_jobs
)

# Define module-level constants
Msft365_USER_LABEL = "Msft365User"
Msft365_GROUP_LABEL = "Msft365Group"
Msft365_OU_LABEL = "Msft365OrganizationalUnit"
Msft_DEVICE_LABEL = "Msft365Device"

Msft365_MEMBER_OF_RELATIONSHIP = "MEMBER_OF"
Msft365_PART_OF_RELATIONSHIP = "PART_OF"
Msft365_OWNED_BY_RELATIONSHIP = "OWNED_BY"

logger = logging.getLogger(__name__)

def start_Msft365_ingestion(
    neo4j_session,
    config: Dict,
    common_job_parameters: Dict,
) -> None:
    """
    Starts the Msft365 data ingestion process.
    
    :param neo4j_session: The Neo4j session.
    :param config: A dictionary containing necessary Msft365 credentials and configuration.
    :param common_job_parameters: Parameters to be passed to each Neo4j job.
    :return: None
    """
    tenant_id = config.get('Msft365_tenant_id')
    client_id = config.get('Msft365_client_id')
    client_secret = config.get('Msft365_client_secret')
    
    if not (tenant_id and client_id and client_secret):
        logger.warning(
            "Msft365 credentials are not configured correctly. Make sure Msft365_tenant_id, "
            "Msft365_client_id, and Msft365_client_secret are set in the config."
        )
        return
    
    logger.info("Starting Msft365 sync")
    
    # Get update tag
    update_tag = common_job_parameters.get('UPDATE_TAG')
    
    try:
        # Get access token once
        access_token = get_access_token(tenant_id, client_id, client_secret)

        # Sync users from Msft365
        logger.info("Syncing Msft365 users")
        users = sync_Msft365_users(
            neo4j_session, access_token, update_tag, common_job_parameters
        )
        
        # Sync groups from Msft365
        logger.info("Syncing Msft365 groups")
        groups = sync_Msft365_groups(
            neo4j_session, access_token, update_tag, common_job_parameters
        )
        
        # Sync organizational units from Msft365
        logger.info("Syncing Msft365 organizational units")
        ous = sync_Msft365_organizational_units(
            neo4j_session, access_token, update_tag, common_job_parameters
        )
        
        # Sync devices from Msft365
        logger.info("Syncing Msft365 devices")
        devices = sync_Msft365_devices(
            neo4j_session, access_token, update_tag, common_job_parameters
        )
        
        # Sync device relationships
        logger.info("Syncing device ownership relationships")
        sync_Msft365_devices(
            neo4j_session, access_token, devices, users, update_tag, common_job_parameters
        )

        # Sync relationships between users and groups
        logger.info("Syncing Msft365 user-group relationships")
        sync_Msft365_user_group_relationships(
            neo4j_session, access_token, groups, update_tag, common_job_parameters
        )
        
        # Sync relationships between OUs and other entities
        logger.info("Syncing Msft365 organizational unit relationships")
        sync_Msft365_ou_relationships(
            neo4j_session, access_token, ous, update_tag, common_job_parameters
        )

        # Sync device relationships
        logger.info("Syncing device ownership relationships")
        sync_Msft365_device_relationships(
            neo4j_session, access_token, devices, users, update_tag, common_job_parameters
        )
        
        # Run cleanup to remove stale data
        logger.info("Running Msft365 cleanup jobs")
        run_cleanup_jobs(
            neo4j_session, update_tag, common_job_parameters
        )

        
        logger.info("Msft365 sync complete")
        
    except Exception as e:
        logger.error(f"Error syncing data from Msft365: {e}")
        raise
