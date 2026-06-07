import neo4j

from cartography.client.core.tx import load
from cartography.models.jamf.tenant import JamfTenantSchema


def load_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        JamfTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
