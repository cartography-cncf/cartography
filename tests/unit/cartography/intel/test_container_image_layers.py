from unittest.mock import MagicMock

import pytest

from cartography.intel import container_image_layers
from cartography.intel.container_image_layers import ContainerImageLayerGraphShape
from cartography.intel.container_image_layers import get_complete_layer_digests
from cartography.intel.container_image_layers import partition_layer_fetches
from cartography.intel.container_image_layers import refresh_layer_closures

TEST_SHAPE = ContainerImageLayerGraphShape(
    image_label="TestImage",
    layer_label="TestImageLayer",
    scope_label="TestTenant",
    scope_properties=("id",),
    has_next=True,
)


def test_graph_shape_rejects_unsafe_cypher_identifiers():
    # Act and assert
    with pytest.raises(ValueError, match="Invalid Cypher identifier"):
        ContainerImageLayerGraphShape(
            image_label="TestImage) MATCH (n",
            layer_label="TestImageLayer",
            scope_label="TestTenant",
            scope_properties=("id",),
        )


def test_partition_layer_fetches_preserves_candidate_order():
    # Arrange
    candidates = [
        {"digest": "sha256:new"},
        {"digest": "sha256:complete"},
        {"name": "missing-digest"},
    ]

    # Act
    to_fetch, to_refresh = partition_layer_fetches(
        candidates,
        {"sha256:complete"},
    )

    # Assert
    assert to_fetch == [
        {"digest": "sha256:new"},
        {"name": "missing-digest"},
    ]
    assert to_refresh == [{"digest": "sha256:complete"}]


def test_get_complete_layer_digests_accepts_empty_layer_lists():
    # Arrange
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = [
        "sha256:with-layers",
        "sha256:scratch",
    ]

    # Act
    result = get_complete_layer_digests(
        neo4j_session,
        TEST_SHAPE,
        ["sha256:with-layers", "sha256:scratch"],
        {"id": "tenant-1"},
    )

    # Assert
    assert result == {"sha256:with-layers", "sha256:scratch"}
    query = neo4j_session.execute_read.call_args.args[1]
    assert "img.layer_diff_ids IS NOT NULL" in query
    assert "size(img.layer_diff_ids) = 0" in query
    assert "size(img.layer_diff_ids) > 0" not in query
    assert "MATCH (img)-[:HAS_LAYER]->" in query
    assert "MATCH (img)-[:HEAD]->" in query
    assert "MATCH (img)-[:TAIL]->" in query
    assert "})-[:NEXT]->(" in query


def test_refresh_layer_closures_updates_the_full_existing_closure(monkeypatch):
    # Arrange
    run_write_query = MagicMock()
    monkeypatch.setattr(container_image_layers, "run_write_query", run_write_query)
    neo4j_session = MagicMock()

    # Act
    refresh_layer_closures(
        neo4j_session,
        TEST_SHAPE,
        {"sha256:image"},
        {"id": "tenant-1"},
        456,
    )

    # Assert
    assert run_write_query.call_count == 6
    queries = "\n".join(call.args[1] for call in run_write_query.call_args_list)
    assert "resource.lastupdated = $update_tag" in queries
    assert "layer.lastupdated = $update_tag" in queries
    assert "type(relationship) IN $relationship_types" in queries
    assert "[relationship:NEXT]" in queries
    assert all(
        call.kwargs["update_tag"] == 456 for call in run_write_query.call_args_list
    )


def test_refresh_layer_closures_batches_all_writes(monkeypatch):
    run_write_query = MagicMock()
    monkeypatch.setattr(container_image_layers, "run_write_query", run_write_query)
    digests = [f"sha256:{index}" for index in range(1201)]

    refresh_layer_closures(
        MagicMock(),
        TEST_SHAPE,
        digests,
        {"id": "tenant-1"},
        456,
        batch_size=500,
    )

    assert run_write_query.call_count == 18
    assert all(
        len(call.kwargs["digests"]) <= 500 for call in run_write_query.call_args_list
    )
    assert {
        digest
        for call in run_write_query.call_args_list[::6]
        for digest in call.kwargs["digests"]
    } == set(digests)


def test_refresh_layer_closures_rejects_invalid_batch_size():
    with pytest.raises(ValueError, match="batch_size"):
        refresh_layer_closures(
            MagicMock(),
            TEST_SHAPE,
            ["sha256:image"],
            {"id": "tenant-1"},
            456,
            batch_size=0,
        )
