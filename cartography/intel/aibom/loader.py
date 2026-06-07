from neo4j import Session

from cartography.client.core.tx import load
from cartography.models.aibom.component import AIBOMComponentSchema
from cartography.models.aibom.source import AIBOMSourceSchema


def load_aibom_sources(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AIBOMSourceSchema(),
        source_payloads,
        lastupdated=update_tag,
    )


def load_aibom_components(
    neo4j_session: Session,
    component_payloads: list[dict[str, object]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AIBOMComponentSchema(),
        component_payloads,
        lastupdated=update_tag,
    )
