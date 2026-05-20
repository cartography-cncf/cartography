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


def load_aibom_uses_model_relationships(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    source_key: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        AIBOMComponentUsesModelRel(),
        source_payloads,
        lastupdated=update_tag,
        _sub_resource_label="AIBOMSource",
        _sub_resource_id=source_key,
    )


def load_aibom_uses_tool_relationships(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    source_key: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        AIBOMComponentUsesToolRel(),
        source_payloads,
        lastupdated=update_tag,
        _sub_resource_label="AIBOMSource",
        _sub_resource_id=source_key,
    )


def load_aibom_exposes_tool_relationships(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    source_key: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        AIBOMComponentExposesToolRel(),
        source_payloads,
        lastupdated=update_tag,
        _sub_resource_label="AIBOMSource",
        _sub_resource_id=source_key,
    )


def load_aibom_custom_relationships(
    neo4j_session: Session,
    source_payloads: list[dict[str, object]],
    source_key: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        AIBOMComponentCustomRel(),
        source_payloads,
        lastupdated=update_tag,
        _sub_resource_label="AIBOMSource",
        _sub_resource_id=source_key,
    )
