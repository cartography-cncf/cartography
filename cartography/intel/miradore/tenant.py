import neo4j

from cartography.client.core.tx import load
from cartography.models.miradore.tenant import MiradoreTenantSchema


def load_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        MiradoreTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
