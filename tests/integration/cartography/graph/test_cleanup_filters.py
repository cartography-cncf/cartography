from collections.abc import Iterator

import neo4j
import pytest

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@pytest.fixture(autouse=True)  # type: ignore[misc]
def clean_graph(neo4j_session: neo4j.Session) -> Iterator[None]:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n")


def test_filtered_cleanup_preserves_other_owners_sources_and_accounts(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange
    neo4j_session.run(
        "CREATE (:SubResource {id:'a'}), (:SubResource {id:'b'}), (:HelloAsset {id:'hello'}), (:WorldAsset {id:'world'})"
    )
    data = [
        {
            "Id": name,
            "property1": owner,
            "property2": source,
            "hello_asset_id": "hello",
            "world_asset_id": "world",
        }
        for name, owner, source in [
            ("stale-1", "healthy", "source-a"),
            ("stale-2", "healthy", "source-a"),
            ("current", "healthy", "source-a"),
            ("denied", "denied", "source-a"),
            ("other-source", "healthy", "source-b"),
        ]
    ]
    load(
        neo4j_session,
        InterestingAssetSchema(),
        data,
        lastupdated=1,
        sub_resource_id="a",
    )
    load(
        neo4j_session,
        InterestingAssetSchema(),
        [{**data[0], "Id": "other-account"}],
        lastupdated=1,
        sub_resource_id="b",
    )
    load(
        neo4j_session,
        InterestingAssetSchema(),
        [{"Id": "current", "property1": "healthy", "property2": "source-a"}],
        lastupdated=2,
        sub_resource_id="a",
    )

    # Act: one-record batches exercise iteration for node and relationship cleanup.
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "a"},
        iterationsize=1,
        node_filters={"property1": "healthy", "property2": "source-a"},
    ).run(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "InterestingAsset", ["id", "lastupdated"]) == {
        ("current", 2),
        ("denied", 1),
        ("other-source", 1),
        ("other-account", 1),
    }
    assert check_rels(
        neo4j_session,
        "SubResource",
        "id",
        "InterestingAsset",
        "id",
        "RELATIONSHIP_LABEL",
    ) == {
        ("a", "current"),
        ("a", "denied"),
        ("a", "other-source"),
        ("b", "other-account"),
    }
    assert check_rels(
        neo4j_session, "InterestingAsset", "id", "HelloAsset", "id", "ASSOCIATED_WITH"
    ) == {(name, "hello") for name in ("denied", "other-source", "other-account")}
    assert check_rels(
        neo4j_session, "WorldAsset", "id", "InterestingAsset", "id", "CONNECTED"
    ) == {("world", name) for name in ("denied", "other-source", "other-account")}


def test_authoritative_orphan_cleanup_deletes_current_nodes_and_handles_empty_inventory(
    neo4j_session: neo4j.Session,
) -> None:
    # Arrange: orphan records may share the current update tag.
    neo4j_session.run("CREATE (:SubResource {id:'a'}), (:SubResource {id:'b'})")
    data = [
        {"Id": name, "property1": owner, "property2": source}
        for name, owner, source in [
            ("keep", "present", "source-a"),
            ("orphan-1", "removed", "source-a"),
            ("orphan-2", "removed", "source-a"),
            ("other-source", "removed", "source-b"),
        ]
    ]
    load(
        neo4j_session,
        InterestingAssetSchema(),
        data,
        lastupdated=2,
        sub_resource_id="a",
    )
    load(
        neo4j_session,
        InterestingAssetSchema(),
        [{**data[1], "Id": "other-account"}],
        lastupdated=2,
        sub_resource_id="b",
    )

    # Act
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "a"},
        iterationsize=1,
        node_filters={"property2": "source-a"},
        excluded_node_filters={"property1": ["present"]},
        delete_current=True,
    ).run(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == {
        ("keep",),
        ("other-source",),
        ("other-account",),
    }

    # Act: empty inventory excludes nothing, retaining the other source/account scope.
    GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {"UPDATE_TAG": 2, "sub_resource_id": "a"},
        iterationsize=1,
        node_filters={"property2": "source-a"},
        excluded_node_filters={"property1": []},
        delete_current=True,
    ).run(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "InterestingAsset", ["id"]) == {
        ("other-source",),
        ("other-account",),
    }
    assert check_rels(
        neo4j_session,
        "SubResource",
        "id",
        "InterestingAsset",
        "id",
        "RELATIONSHIP_LABEL",
    ) == {("a", "other-source"), ("b", "other-account")}
