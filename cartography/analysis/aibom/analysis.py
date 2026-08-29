from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement

AIBOM_RUNS_ON_CONTAINER = AnalysisJob(
    name="AIBOMSource RUNS_ON Container analysis",
    short_name="aibom_runs_on_container_analysis",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (a:AIBOMSource)-[:SCANNED_IMAGE]->(i:Image)<-[:RESOLVED_IMAGE]-(c:Container)",
            effects=(
                AddRelationship(
                    "a",
                    "RUNS_ON",
                    "c",
                    source_label="AIBOMSource",
                    target_label="Container",
                ),
            ),
        ),
    ),
)
