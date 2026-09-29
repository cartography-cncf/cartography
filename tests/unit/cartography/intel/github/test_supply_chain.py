from unittest.mock import MagicMock

from cartography.intel.github.supply_chain import (
    get_unmatched_container_images_with_history,
)


def test_get_unmatched_container_images_limits_before_layer_history_expansion():
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.run.return_value = []

    # Act
    get_unmatched_container_images_with_history(
        neo4j_session,
        organization="example",
        update_tag=1,
        limit=10,
    )

    # Assert
    query = neo4j_session.run.call_args.args[0]
    assert (
        query.index("ORDER BY coalesce(repo.uri, img.digest)")
        < query.index("LIMIT 10")
        < query.index("UNWIND range")
    )
