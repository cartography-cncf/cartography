from collections import defaultdict

from neo4j import Session

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.models.aibom.component import AIBOMComponentCustomRel
from cartography.models.aibom.component import AIBOMComponentExposesToolRel
from cartography.models.aibom.component import AIBOMComponentSchema
from cartography.models.aibom.component import AIBOMComponentUsesModelRel
from cartography.models.aibom.component import AIBOMComponentUsesToolRel
from cartography.models.aibom.source import AIBOMSourceSchema


def load_aibom_sources(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    update_tag: int,
) -> None:
    if source_payloads:
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
    if component_payloads:
        load(
            neo4j_session,
            AIBOMComponentSchema(),
            component_payloads,
            lastupdated=update_tag,
        )


def load_aibom_component_relationships(
    neo4j_session: Session,
    relationship_payloads: list[dict[str, object]],
    relationship_label: str,
    update_tag: int,
) -> None:
    rel_schema_map = {
        "USES_MODEL": AIBOMComponentUsesModelRel(),
        "USES_TOOL": AIBOMComponentUsesToolRel(),
        "EXPOSES_TOOL": AIBOMComponentExposesToolRel(),
        "CUSTOM": AIBOMComponentCustomRel(),
    }
    rel_schema = rel_schema_map[relationship_label]

    payloads_by_source_key: dict[str, list[dict[str, object]]] = defaultdict(list)
    for relationship_payload in relationship_payloads:
        if relationship_payload.get("relationship_label") != relationship_label:
            continue

        source_key = relationship_payload.get("source_key")
        if isinstance(source_key, str):
            payloads_by_source_key[source_key].append(relationship_payload)

    for source_key, source_payloads in payloads_by_source_key.items():
        load_matchlinks(
            neo4j_session,
            rel_schema,
            source_payloads,
            lastupdated=update_tag,
            _sub_resource_label="AIBOMSource",
            _sub_resource_id=source_key,
        )
