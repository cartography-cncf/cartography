import logging
from typing import Dict

import neo4j

from cartography.util import timeit
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.tenant import AzureTenantSchema
from cartography.models.azure.principal import AzurePrincipalSchema

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
    load(
        neo4j_session,
        AzureTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        AzurePrincipalSchema(),
        [{"current_user": current_user}],
        lastupdated=update_tag,
        AZURE_TENANT_ID=tenant_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(AzurePrincipalSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AzureTenantSchema(), common_job_parameters).run(
        neo4j_session,
    )


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
