from typing import Any

from neo4j import Session

from cartography.graph.job import GraphJob
from cartography.models.aibom import AIBOMComponentSchema
from cartography.models.aibom import AIBOMSourceSchema
from cartography.models.aibom import AIBOMWorkflowSchema


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
    GraphJob.from_node_schema(AIBOMWorkflowSchema(), common_job_parameters).run(
        neo4j_session,
    )
