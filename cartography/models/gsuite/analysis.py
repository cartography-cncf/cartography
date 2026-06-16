from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import RelationshipEffect

GSUITE_HUMAN_LINK = AnalysisJob(
    name="GSuite user map to Human",
    short_name="gsuite_human_link",
    effect=RelationshipEffect("Human", "IDENTITY_GSUITE", "GSuiteUser"),
    cleanup_iterationsize=100,
    statements=(
        AnalysisStatement(
            "MATCH (human:Human), (guser:GSuiteUser) "
            "WHERE human.email = guser.email "
            "MERGE (human)-[r:IDENTITY_GSUITE]->(guser) "
            "ON CREATE SET r.firstseen = $UPDATE_TAG "
            "SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)
