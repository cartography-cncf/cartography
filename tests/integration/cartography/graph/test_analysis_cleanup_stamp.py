import pytest
from neo4j.exceptions import ClientError

from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import Var
from cartography.util import run_typed_analysis_job
from tests.integration.util import check_nodes

# The write divides by $DIVISOR, so a divisor of 0 makes the write itself fail.
SMALL_NODE_CHECK = AnalysisJob(
    name="Small node check",
    short_name="small_node_check",
    statements=(
        AnalysisStatement(
            match="MATCH (n:StampedCheckNode) WITH n, n.size / $DIVISOR < 10 AS small",
            effects=(
                SetProperties(
                    "n",
                    {"small": Var("small"), "small_checked_at": Param("UPDATE_TAG")},
                    label="StampedCheckNode",
                    cleanup_stamp="small_checked_at",
                ),
            ),
        ),
    ),
)


def test_stamped_results_survive_a_run_whose_write_fails(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n:StampedCheckNode) DETACH DELETE n")
    neo4j_session.run("CREATE (:StampedCheckNode {id: 'node-1', size: 5})")
    run_typed_analysis_job(
        SMALL_NODE_CHECK, neo4j_session, {"UPDATE_TAG": 1, "DIVISOR": 1}
    )

    # Act
    with pytest.raises(ClientError):
        run_typed_analysis_job(
            SMALL_NODE_CHECK, neo4j_session, {"UPDATE_TAG": 2, "DIVISOR": 0}
        )

    # Assert: no cleanup ran before the failed write.
    assert check_nodes(
        neo4j_session, "StampedCheckNode", ["id", "small", "small_checked_at"]
    ) == {("node-1", True, 1)}
