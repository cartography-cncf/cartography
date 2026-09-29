from dataclasses import replace
from typing import Any

import pytest

from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.job import GraphJob
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.graph.querybuilder.sample_models.allow_unscoped import (
    UnscopedNodeSchema,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToSubResourceRel,
)


@pytest.mark.parametrize(  # type: ignore[misc]
    "schema",
    [InterestingAssetSchema(), UnscopedNodeSchema(), GitHubOrganizationUserSchema()],
)
def test_filters_constrain_every_cleanup_query_before_limit(
    schema: CartographyNodeSchema,
) -> None:
    # Act
    queries = build_cleanup_queries(
        schema, node_filters={"id": "a"}, excluded_node_filters={"id": ["b"]}
    )

    # Assert: both node and relationship cleanup retain the same scope restriction.
    assert queries
    for query in queries:
        assert query.index("n.`id` = $_cartography_node_filters.`id`") < query.index(
            "LIMIT $LIMIT_SIZE"
        )
        assert query.index(
            "NOT n.`id` IN $_cartography_excluded_node_filters.`id`"
        ) < query.index("LIMIT $LIMIT_SIZE")


def test_filter_parameters_are_bound_without_mutating_inputs() -> None:
    # Arrange
    parameters = {"UPDATE_TAG": 2, "sub_resource_id": "account"}
    filters = {"property1": "x') DETACH DELETE n //"}
    excluded = {"property2": ["keep"]}

    # Act
    job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        parameters,
        node_filters=filters,
        excluded_node_filters=excluded,
    )
    excluded["property2"].append("later")

    # Assert
    assert parameters == {"UPDATE_TAG": 2, "sub_resource_id": "account"}
    assert filters == {"property1": "x') DETACH DELETE n //"}
    for statement in job.statements:
        assert filters["property1"] not in statement.query
        assert statement.parameters["_cartography_node_filters"] == filters
        assert statement.parameters["_cartography_excluded_node_filters"] == {
            "property2": ["keep"]
        }


@pytest.mark.parametrize(  # type: ignore[misc]
    "options",
    [
        {"node_filters": {"unknown": "x"}},
        {"node_filters": {"id": None}},
        {"excluded_node_filters": {"id` OR true //": []}},
        {"delete_current": True},
        {"delete_current": True, "node_filters": {}, "excluded_node_filters": {}},
    ],
)
def test_invalid_cleanup_filters_are_rejected(options: dict[str, Any]) -> None:
    # Act and assert
    with pytest.raises(ValueError):
        GraphJob.from_node_schema(
            InterestingAssetSchema(),
            {"UPDATE_TAG": 2, "sub_resource_id": "account"},
            **options,
        )


def test_relationship_only_cleanup_rejects_delete_current() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="relationship-only cleanup"):
        GraphJob.from_node_schema(
            GitHubOrganizationUserSchema(),
            {"UPDATE_TAG": 2},
            node_filters={"id": "orphan"},
            delete_current=True,
        )


@pytest.mark.parametrize(  # type: ignore[misc]
    "reserved,options",
    [
        ("_cartography_node_filters", {"node_filters": {"id": "x"}}),
        ("_cartography_excluded_node_filters", {"excluded_node_filters": {"id": []}}),
    ],
)
def test_reserved_filter_parameter_collisions_are_rejected(
    reserved: str, options: dict[str, Any]
) -> None:
    # Arrange
    parameters = {
        "UPDATE_TAG": 2,
        "sub_resource_id": "account",
        reserved: "caller-owned",
    }

    # Act and assert
    with pytest.raises(ValueError, match="parameter collision"):
        GraphJob.from_node_schema(InterestingAssetSchema(), parameters, **options)
    assert parameters[reserved] == "caller-owned"


def test_schema_parameter_collision_is_not_filled_by_filter_values() -> None:
    # Arrange
    relationship = replace(
        InterestingAssetToSubResourceRel(),
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_cartography_node_filters", set_in_kwargs=True)}
        ),
    )
    schema = replace(InterestingAssetSchema(), sub_resource_relationship=relationship)

    # Act and assert
    with pytest.raises(ValueError, match="parameter collision"):
        GraphJob.from_node_schema(schema, {"UPDATE_TAG": 2}, node_filters={"id": "x"})


def test_authoritative_empty_exclusion_omits_only_node_staleness() -> None:
    # Act
    queries = build_cleanup_queries(
        InterestingAssetSchema(),
        excluded_node_filters={"property1": []},
        delete_current=True,
    )

    # Assert
    assert "n.lastupdated <> $UPDATE_TAG" not in queries[0]
    assert (
        "NOT n.`property1` IN $_cartography_excluded_node_filters.`property1`"
        in queries[0]
    )
    assert "s.lastupdated <> $UPDATE_TAG" in queries[1]
    assert all("r.lastupdated <> $UPDATE_TAG" in query for query in queries[2:])
