import logging
import neo4j
from cartography.config import Config
from cartography.intel.microsoft_defender import machines
from cartography.intel.microsoft_defender.client import MDEClient

logger = logging.getLogger(__name__)


def start_microsoft_defender_ingestion(
    neo4j_session: neo4j.Session, config: Config
) -> None:
    # Use a dummy ID for prototype; later this comes from config.mde_tenant_id
    tenant_id = "test-tenant-id-123"
    update_tag = config.update_tag

    common_job_parameters = {"UPDATE_TAG": update_tag, "tenant_id": tenant_id}

    client = MDEClient(tenant_id)

    machines.sync(neo4j_session, client, tenant_id, update_tag, common_job_parameters)
