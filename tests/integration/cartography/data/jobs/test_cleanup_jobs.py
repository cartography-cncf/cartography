from unittest import mock

import cartography.util
from cartography.util import run_cleanup_job

UPDATE_TAG_T1 = 111111
UPDATE_TAG_T2 = 222222
UPDATE_TAG_T3 = 333333
UPDATE_TAG_T4 = 444444


SAMPLE_CLEANUP_JOB = """
{
  "statements": [
    {
      "query": "MATCH(:TypeA)-[r:REL]->(:TypeB) WHERE r.lastupdated <> $UPDATE_TAG WITH r LIMIT $LIMIT_SIZE DELETE r",
      "iterative": true,
      "iterationsize": 100
    },{
      "query": "MATCH (n:TypeA) WHERE n.lastupdated <> $UPDATE_TAG WITH n LIMIT $LIMIT_SIZE DETACH DELETE (n)",
      "iterative": true,
      "iterationsize": 100
    },{
      "query": "MATCH (n:TypeB) WHERE n.lastupdated <> $UPDATE_TAG WITH n LIMIT $LIMIT_SIZE DETACH DELETE (n)",
      "iterative": true,
      "iterationsize": 100
    }],
  "name": "cleanup stale resources"
}
"""

SAMPLE_JOB_FILENAME = "/path/to/this/cleanupjob/mycleanupjob.json"


@mock.patch.object(cartography.util, "read_text", return_value=SAMPLE_CLEANUP_JOB)
def test_run_cleanup_job_on_relationships(
    mock_read_text: mock.MagicMock,
    neo4j_session,
):
    # Arrange: nodes id1 and id2 are connected to each other at time T2 via stale RELship r
    neo4j_session.run(
        """
        MERGE (a:TypeA{id:"id1", lastupdated:$UPDATE_TAG_T2})-[r:REL{lastupdated:$UPDATE_TAG_T1}]->
              (b:TypeB{id:"id2", lastupdated:$UPDATE_TAG_T2})
        """,
        UPDATE_TAG_T1=UPDATE_TAG_T1,
        UPDATE_TAG_T2=UPDATE_TAG_T2,
    )

    # Act: delete all nodes and rels where `lastupdated` != UPDATE_TAG_T2
    job_parameters = {"UPDATE_TAG": UPDATE_TAG_T2}
    run_cleanup_job(SAMPLE_JOB_FILENAME, neo4j_session, job_parameters)

    # Assert 1: Node id1 is no longer attached to Node id2
    nodes = neo4j_session.run(
        """
        MATCH (a:TypeA)
        OPTIONAL MATCH (a)-[r:REL]->(b:TypeB)
        RETURN a.id, r.lastupdated, b.id
        """,
    )
    actual_nodes = {(n["a.id"], n["r.lastupdated"], n["b.id"]) for n in nodes}
    expected_nodes = {
        ("id1", None, None),
    }
    assert actual_nodes == expected_nodes

    # Assert 2: Node id2 still exists
    nodes = neo4j_session.run(
        """
        MATCH (b:TypeB) RETURN b.id, b.lastupdated
        """,
    )
    actual_nodes = {(n["b.id"], n["b.lastupdated"]) for n in nodes}
    expected_nodes = {
        ("id2", UPDATE_TAG_T2),
    }
    assert actual_nodes == expected_nodes
    mock_read_text.assert_called_once()


@mock.patch.object(cartography.util, "read_text", return_value=SAMPLE_CLEANUP_JOB)
def test_run_cleanup_job_on_nodes(mock_read_text: mock.MagicMock, neo4j_session):
    # Arrange: we are now at time T3, and node id1 exists but node id2 no longer exists
    neo4j_session.run(
        """
        MATCH (a:TypeA{id:"id1"}) SET a.lastupdated=$UPDATE_TAG_T3
        """,
        UPDATE_TAG_T3=UPDATE_TAG_T3,
    )

    # Act: delete all nodes and rels where `lastupdated` != UPDATE_TAG_T3
    job_parameters = {"UPDATE_TAG": UPDATE_TAG_T3}
    run_cleanup_job(SAMPLE_JOB_FILENAME, neo4j_session, job_parameters)

    # Assert: Node id1 is the only node that still exists
    nodes = neo4j_session.run(
        """
        MATCH (n) RETURN n.id, n.lastupdated
        """,
    )
    actual_nodes = {(n["n.id"], n["n.lastupdated"]) for n in nodes}
    expected_nodes = {
        ("id1", UPDATE_TAG_T3),
    }
    assert actual_nodes == expected_nodes
    mock_read_text.assert_called_once()


@mock.patch.object(cartography.util, "read_text", return_value=SAMPLE_CLEANUP_JOB)
def test_run_cleanup_job_iterative_multiple_batches(
    mock_read_text: mock.MagicMock,
    neo4j_session,
):
    # Arrange: load 300 nodes to the graph
    for i in range(300):
        neo4j_session.run(
            """
            MATCH (a:TypeA{id:$Id}) SET a.lastupdated=$UPDATE_TAG_T3
            """,
            Id=i,
            UPDATE_TAG_T3=UPDATE_TAG_T3,
        )

    # Act: delete all nodes and rels where `lastupdated` != UPDATE_TAG_T4.
    job_parameters = {"UPDATE_TAG": UPDATE_TAG_T4}
    run_cleanup_job(SAMPLE_JOB_FILENAME, neo4j_session, job_parameters)

    # Assert: There are no nodes of label :TypeA in the graph, as the job iteratively removed them.
    nodes = neo4j_session.run(
        """
        MATCH (n:TypeA) RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == set()
    mock_read_text.assert_called_once()
