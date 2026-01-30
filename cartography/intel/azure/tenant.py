import logging
from typing import Dict
from typing import Optional

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.principal import AzurePrincipalSchema

# Import the new, separated schemas
from cartography.models.azure.tenant import AzureTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def load_azure_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    current_user: Optional[str],
    update_tag: int,
) -> None:
    """
    Ingest the Azure Tenant and, if available, the Azure Principal into Neo4j.
    """
    tenant_data = {"id": tenant_id}
    load(neo4j_session, AzureTenantSchema(), [tenant_data], lastupdated=update_tag)

    if current_user:
        principal_data = {"id": current_user}
        load(
            neo4j_session,
            AzurePrincipalSchema(),
            [principal_data],
            lastupdated=update_tag,
            TENANT_ID=tenant_id,
        )


@timeit
def cleanup_azure_tenant(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Delete stale Azure Tenants and Principals.
    """
    GraphJob.from_node_schema(AzureTenantSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AzurePrincipalSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    current_user: Optional[str],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure tenant '%s'.", tenant_id)
    load_azure_tenant(neo4j_session, tenant_id, current_user, update_tag)
    cleanup_azure_tenant(neo4j_session, common_job_parameters)
