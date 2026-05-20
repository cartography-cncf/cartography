from typing import Any

from neo4j import Session

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.aibom.component import AIBOMComponentCustomRel
from cartography.models.aibom.component import AIBOMComponentExposesToolRel
from cartography.models.aibom.component import AIBOMComponentSchema
from cartography.models.aibom.component import AIBOMComponentUsesModelRel
from cartography.models.aibom.component import AIBOMComponentUsesToolRel
from cartography.models.aibom.source import AIBOMSourceSchema

_AIBOM_SOURCE_KEYS_QUERY = """
    MATCH (s:AIBOMSource)
    WHERE s.lastupdated = $UPDATE_TAG
    RETURN s.source_key AS source_key
"""


def cleanup_aibom(
    neo4j_session: Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(AIBOMSourceSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AIBOMComponentSchema(), common_job_parameters).run(
        neo4j_session,
    )

    # AIBOM component-to-component matchlinks are scoped by source_key rather than
    # a top-level tenant/account id passed into sync, so we query the current run's
    # ingested AIBOMSource nodes to discover which matchlink scopes need cleanup.
    source_keys = [
        row["source_key"]
        for row in neo4j_session.execute_read(
            read_list_of_dicts_tx,
            _AIBOM_SOURCE_KEYS_QUERY,
            UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        )
    ]
    for source_key in source_keys:
        GraphJob.from_matchlink(
            AIBOMComponentUsesModelRel(),
            "AIBOMSource",
            source_key,
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
        GraphJob.from_matchlink(
            AIBOMComponentUsesToolRel(),
            "AIBOMSource",
            source_key,
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
        GraphJob.from_matchlink(
            AIBOMComponentExposesToolRel(),
            "AIBOMSource",
            source_key,
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
        GraphJob.from_matchlink(
            AIBOMComponentCustomRel(),
            "AIBOMSource",
            source_key,
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
