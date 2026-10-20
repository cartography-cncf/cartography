from types import SimpleNamespace
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.graph.statement import GraphStatement

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

    restored = GraphStatement.create_from_json(statement.as_dict())

    assert restored.batched_transactions
    assert (
        restored.parameters["SCAN_LIMIT_SIZE"]
        == statement.parameters["SCAN_LIMIT_SIZE"]
    )


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
