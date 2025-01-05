from unittest.mock import MagicMock

from cartography.client.core.tx import load
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
