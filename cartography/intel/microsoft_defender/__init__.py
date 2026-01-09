import logging
from cartography.util import run_cleanup_job
from cartography.config import Config
from cartography.intel.microsoft_defender import machines

logger = logging.getLogger(__name__)

def start_mde_ingestion(neo4j_session, config: Config):
    """
    Starts the MDE ingestion process.
    """
    # 1. Validate that the Tenant ID is present
    if not config.mde_tenant_id:
        logger.error("MDE Tenant ID is missing. Please provide --mde-tenant-id.")
        return

    tenant_id = config.mde_tenant_id
    
    # 2. Proceed with the sync using the real ID
    logger.info(f"Starting MDE sync for tenant {tenant_id}")
    
    # (Your existing sync logic calls go here)
    machines.sync(neo4j_session, config, tenant_id)