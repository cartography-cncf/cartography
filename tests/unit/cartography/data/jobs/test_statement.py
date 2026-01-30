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
