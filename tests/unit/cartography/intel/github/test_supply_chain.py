from unittest.mock import MagicMock

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.intel.github.supply_chain import (
    get_unmatched_container_images_with_history,
)


def test_get_unmatched_container_images_limits_before_layer_history_expansion():
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = []

    # Act
    get_unmatched_container_images_with_history(
        neo4j_session,
        organization="example",
        update_tag=1,
        limit=10,
    )

    # Assert
    tx_func, query = neo4j_session.execute_read.call_args.args[:2]
    assert tx_func is read_list_of_dicts_tx
    assert (
        query.index("ORDER BY coalesce(repo.uri, img.digest)")
        < query.index("LIMIT 10")
        < query.index("UNWIND range")
    )
