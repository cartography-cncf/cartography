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


@patch("cartography.graph.statement.execute_write_with_retry")
def test_run_noniterative_uses_retry_wrapper(mock_execute_write_with_retry):
    statement = GraphStatement("RETURN 1")
    session = MagicMock()

    statement.run(session)

    mock_execute_write_with_retry.assert_called_once_with(
        session,
        statement._run_noniterative,
    )


@patch("cartography.graph.statement.execute_write_with_retry")
def test_run_iterative_uses_retry_wrapper(mock_execute_write_with_retry):
    statement = GraphStatement("RETURN 1", iterative=True, iterationsize=100)
    session = MagicMock()

    first_summary = MagicMock()
    first_summary.counters.contains_updates = True
    second_summary = MagicMock()
    second_summary.counters.contains_updates = False
    mock_execute_write_with_retry.side_effect = [first_summary, second_summary]

    statement.run(session)

    assert mock_execute_write_with_retry.call_count == 2
    mock_execute_write_with_retry.assert_any_call(
        session,
        statement._run_noniterative,
    )
