import json
from types import SimpleNamespace
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.graph.statement import GraphStatement
from cartography.graph.statement import GraphStatementJSONEncoder
from cartography.graph.statement import SCAN_BATCHES_PER_RUN

SAMPLE_STATEMENT_AS_DICT = {
    "query": "Query goes here",
    "iterative": False,
}


def test_create_from_json():
    statement: GraphStatement = GraphStatement.create_from_json(
        SAMPLE_STATEMENT_AS_DICT,
        "my_job_name",
        1,
    )
    assert statement.parent_job_name == "my_job_name"
    assert statement.query == "Query goes here"
    assert statement.parent_job_sequence_num == 1


def test_create_from_json_keeps_batched_transactions():
    statement = GraphStatement(
        "Query goes here", iterationsize=5, batched_transactions=True
    )

    restored = GraphStatement.create_from_json(
        json.loads(json.dumps(statement, cls=GraphStatementJSONEncoder)),
    )

    assert restored.batched_transactions
    assert restored.parameters["SCAN_LIMIT_SIZE"] == 5 * SCAN_BATCHES_PER_RUN


@patch("cartography.graph.statement.execute_write_with_retry")
def test_run_iterative_uses_retryable_write_until_no_updates(
    mock_execute_write_with_retry,
):
    statement = GraphStatement(
        "Query goes here",
        iterative=True,
        iterationsize=100,
        parent_job_name="my_job_name",
        parent_job_sequence_num=1,
    )
    session = MagicMock()
    mock_execute_write_with_retry.side_effect = [
        SimpleNamespace(counters=SimpleNamespace(contains_updates=True)),
        SimpleNamespace(counters=SimpleNamespace(contains_updates=False)),
    ]

    statement.run(session)

    assert statement.parameters["LIMIT_SIZE"] == 100
    assert mock_execute_write_with_retry.call_args_list == [
        call(session, statement._run_noniterative),
        call(session, statement._run_noniterative),
    ]


def test_statement_keeps_its_batch_size_when_another_statement_shared_its_parameters():
    # Arrange: a sync builds a cleanup statement with a small batch from the
    # parameters it later passes to another job.
    shared_parameters = {"UPDATE_TAG": 1}
    GraphStatement(
        "MATCH (n) RETURN n",
        parameters=shared_parameters,
        iterationsize=1000,
        batched_transactions=True,
    )
    statement = GraphStatement(
        "MATCH (n) RETURN n",
        iterationsize=10000,
        batched_transactions=True,
    )

    # Act
    statement.merge_parameters(shared_parameters)

    # Assert
    assert statement.parameters["LIMIT_SIZE"] == 10000
    assert statement.parameters["SCAN_LIMIT_SIZE"] == 10000 * SCAN_BATCHES_PER_RUN
