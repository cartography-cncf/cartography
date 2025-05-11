import logging
from typing import Dict

import neo4j

from cartography.util import run_cleanup_job
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_tenant_id(credentials: Credentials) -> str:
    return credentials.get_tenant_id()


def load_azure_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    current_user: str,
    update_tag: int,
) -> None:
    query = """
    MERGE (at:AzureTenant{id: $TENANT_ID})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = $update_tag
    WITH at
    MERGE (ap:AzurePrincipal{id: $CURRENT_USER})
    ON CREATE SET ap.email = $CURRENT_USER, ap.firstseen = timestamp()
    SET ap.lastupdated = $update_tag
    WITH at, ap
    MERGE (at)-[r:RESOURCE]->(ap)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag;
    """
    neo4j_session.run(
        query,
        TENANT_ID=tenant_id,
        CURRENT_USER=current_user,
        update_tag=update_tag,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_tenant_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    current_user: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    load_azure_tenant(neo4j_session, tenant_id, current_user, update_tag)
    cleanup(neo4j_session, common_job_parameters)
