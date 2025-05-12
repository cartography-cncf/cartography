from pytest import raises

from cartography.graph.querybuilder import filter_selected_relationships
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToSubResourceRel,
)
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema


def test_filter_selected_rels_raises_value_err():
    """
    Specify a RelSchema that is not present on a given NodeSchema -> expect exception
    """
    # Act and assert
    with raises(ValueError):
        _, _ = filter_selected_relationships(
            SimpleNodeSchema(),
            selected_relationships={InterestingAssetToSubResourceRel()},
        )
