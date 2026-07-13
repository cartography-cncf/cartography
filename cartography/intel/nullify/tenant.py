import logging

import neo4j

from cartography.client.core.tx import load
from cartography.models.nullify.tenant import NullifyTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    """
    Load the NullifyTenant root node. Everything else in the module hangs off this node
    via a RESOURCE sub-resource relationship, so it must be loaded first. The tenant has
    no parent, so there is no cleanup job for it.
    """
    logger.info("Loading Nullify tenant %s", tenant_id)
    load(
        neo4j_session,
        NullifyTenantSchema(),
        [{"id": tenant_id, "name": tenant_id}],
        lastupdated=update_tag,
    )
