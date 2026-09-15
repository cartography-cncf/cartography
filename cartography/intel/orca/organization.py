from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.orca import OrcaOrganizationSchema


def load_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OrcaOrganizationSchema(),
        [organization],
        lastupdated=update_tag,
    )
