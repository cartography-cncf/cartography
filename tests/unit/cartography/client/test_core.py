from unittest.mock import MagicMock

import pytest

from cartography.client.core.tx import load
from cartography.client.core.tx import load_graph_data
from cartography.models.core.nodes import CartographyNodeSchema


def test_load_empty_dict_list():
    # Setup
    mock_session = MagicMock()
    mock_schema = MagicMock(spec=CartographyNodeSchema)
    empty_dict_list = []

    # Execute
    load(mock_session, mock_schema, empty_dict_list)

    # Assert
    mock_session.run.assert_not_called()  # Ensure no database calls were made
    # Verify that ensure_indexes was not called since we short-circuit on empty list
    mock_session.write_transaction.assert_not_called()


def test_load_graph_data_with_zero_batch_size():
    # Arrange
    mock_session = MagicMock()
    query = "MERGE (n:Node {id: $id})"
    dict_list = [{"id": 1}]

    # Act & Assert
    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        load_graph_data(mock_session, query, dict_list, batch_size=0)


def test_load_graph_data_with_negative_batch_size():
    # Arrange
    mock_session = MagicMock()
    query = "MERGE (n:Node {id: $id})"
    dict_list = [{"id": 1}]

    # Act & Assert
    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        load_graph_data(mock_session, query, dict_list, batch_size=-1)
