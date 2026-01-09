import logging
import neo4j
from typing import Dict
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.microsoft_defender.device import MDEDeviceSchema
from cartography.models.microsoft_defender.tenant import MDETenantSchema

logger = logging.getLogger(__name__)


def enrich_azure_risk(neo4j_session: neo4j.Session, update_tag: int):
    """
    Striking Feature: Risk-Based Asset Tagging.
    Finds Azure VMs linked to High Risk MDE devices and tags them as CRITICAL_ASSET.
    """
    query = """
    MATCH (v:AzureVirtualMachine)-[:HAS_DEFENDER_AGENT]->(d:MDEDevice)
    WHERE d.risk_score = 'High'
    SET v.risk_tag = 'CRITICAL_ASSET',
        v.lastupdated = $update_tag
    RETURN count(v) as tagged_count
    """
    logger.info("Running Risk-Based Asset Tagging enrichment...")
    result = neo4j_session.run(query, update_tag=update_tag)
    count = result.single()["tagged_count"]
    logger.info(f"Tagged {count} Azure VMs as CRITICAL_ASSET based on MDE Risk.")


def sync(
    neo4j_session: neo4j.Session,
    mde_client,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: Dict,
):
    logger.info(f"Syncing MDE Machines for tenant {tenant_id}")

    # 1. GET (Now uses the real pagination loop)
    raw_machines = mde_client.get_machines()

    # 2. LOAD Tenant
    load(
        neo4j_session,
        MDETenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
        name="MDE Tenant",
    )

    # 3. LOAD Machines
    load(
        neo4j_session,
        MDEDeviceSchema(),
        raw_machines,
        lastupdated=update_tag,
        tenant_id=tenant_id,
    )

    # 4. CLEANUP
    cleanup_job = GraphJob.from_node_schema(MDEDeviceSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    # 5. ENRICHMENT (The "Extra Mile" Feature)
    enrich_azure_risk(neo4j_session, update_tag)
