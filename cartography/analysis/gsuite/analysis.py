from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param

GSUITE_HUMAN_LINK = AnalysisJob(
    name="GSuite user map to Human",
    short_name="gsuite_human_link",
    cleanup_iterationsize=100,
    statements=(
        AnalysisStatement(
            match="MATCH (human:Human), (guser:GSuiteUser) WHERE human.email = guser.email",
            effects=(
                AddRelationship(
                    "human",
                    "IDENTITY_GSUITE",
                    "guser",
                    firstseen=Param("UPDATE_TAG"),
                    source_label="Human",
                    target_label="GSuiteUser",
                ),
            ),
        ),
    ),
)
