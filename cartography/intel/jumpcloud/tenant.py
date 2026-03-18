import neo4j

from cartography.client.core.tx import load
from cartography.models.jumpcloud.tenant import JumpCloudTenantSchema


def load_tenant(neo4j_session: neo4j.Session, org_id: str, update_tag: int) -> None:
    load(
        neo4j_session,
        JumpCloudTenantSchema(),
        [{"id": org_id}],
        lastupdated=update_tag,
    )
