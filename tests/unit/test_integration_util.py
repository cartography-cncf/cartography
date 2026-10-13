from unittest.mock import MagicMock

import pytest

from tests.integration.util import check_nodes


def test_check_nodes_empty_list_raises_exc():
    # Arrange
    neo4j_session = MagicMock()

    # Act and assert
    with pytest.raises(ValueError):
        check_nodes(neo4j_session, "WorldAsset", [])
