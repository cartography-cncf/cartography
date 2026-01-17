"""
Unit tests for cascade_delete cleanup query generation.

Tests the query builder logic when cascade_delete=True is passed to build_cleanup_queries().
This complements the integration tests in tests/integration/cartography/graph/test_cleanup_cascade.py
by verifying the exact Cypher queries generated.
"""

import pytest

from cartography.graph.cleanupbuilder import _build_cleanup_node_and_rel_queries
from cartography.graph.cleanupbuilder import build_cleanup_queries
from tests.data.graph.querybuilder.sample_models.allow_unscoped import (
    UnscopedNodeSchema,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToHelloAssetRel,
)
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetToSubResourceRel,
)
from tests.unit.cartography.graph.helpers import clean_query_list


def test_cascade_cleanup_sub_rel():
    """
    Test that cascade_delete=True generates the correct cleanup query with OPTIONAL MATCH for children.
    The query should:
    1. Match the parent node attached to its sub resource
    2. Use OPTIONAL MATCH to find children via sub_resource_relationship rel_label
    3. Only delete children that are also stale (lastupdated <> UPDATE_TAG)
    4. Handle parents with no children (empty children list)
    """
    actual_queries: list[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=True,
    )
    expected_queries = [
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        CALL {
            WITH n
            OPTIONAL MATCH (n)<-[:RELATIONSHIP_LABEL]-(child)
            WITH child WHERE child IS NOT NULL AND child.lastupdated <> $UPDATE_TAG
            DETACH DELETE child
        }
        DETACH DELETE n;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;
        """,
    ]
    assert clean_query_list(actual_queries) == clean_query_list(expected_queries)


def test_cascade_cleanup_with_selected_rel():
    """
    Test that cascade_delete=True with a selected relationship generates correct queries.
    The node cleanup query should include cascade logic, while the rel query is unchanged.
    """
    actual_queries: list[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToHelloAssetRel(),
        cascade_delete=True,
    )
    expected_queries = [
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (n)-[r:ASSOCIATED_WITH]->(:HelloAsset)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        CALL {
            WITH n
            OPTIONAL MATCH (n)<-[:RELATIONSHIP_LABEL]-(child)
            WITH child WHERE child IS NOT NULL AND child.lastupdated <> $UPDATE_TAG
            DETACH DELETE child
        }
        DETACH DELETE n;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (n)-[r:ASSOCIATED_WITH]->(:HelloAsset)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    ]
    assert clean_query_list(actual_queries) == clean_query_list(expected_queries)


def test_build_cleanup_queries_with_cascade():
    """
    Test that the full set of cleanup queries with cascade_delete=True is correct.
    The first query should include cascade logic, subsequent rel queries are unchanged.
    """
    actual_queries: list[str] = build_cleanup_queries(
        InterestingAssetSchema(),
        cascade_delete=True,
    )
    expected_queries = [
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        CALL {
            WITH n
            OPTIONAL MATCH (n)<-[:RELATIONSHIP_LABEL]-(child)
            WITH child WHERE child IS NOT NULL AND child.lastupdated <> $UPDATE_TAG
            DETACH DELETE child
        }
        DETACH DELETE n;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (n)-[r:ASSOCIATED_WITH]->(:HelloAsset)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (n)<-[r:CONNECTED]-(:WorldAsset)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    ]
    assert clean_query_list(actual_queries) == clean_query_list(expected_queries)


def test_cascade_delete_default_false():
    """
    Test that cascade_delete defaults to False and produces standard cleanup queries.
    This verifies backward compatibility.
    """
    # Without cascade_delete parameter (default False)
    actual_queries_default: list[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
    )
    # Explicitly setting cascade_delete=False
    actual_queries_explicit: list[str] = _build_cleanup_node_and_rel_queries(
        InterestingAssetSchema(),
        InterestingAssetToSubResourceRel(),
        cascade_delete=False,
    )
    expected_queries = [
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
        """
        MATCH (n:InterestingAsset)<-[s:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE s.lastupdated <> $UPDATE_TAG
        WITH s LIMIT $LIMIT_SIZE
        DELETE s;
        """,
    ]
    assert clean_query_list(actual_queries_default) == clean_query_list(
        expected_queries
    )
    assert clean_query_list(actual_queries_explicit) == clean_query_list(
        expected_queries
    )


def test_cascade_delete_with_unscoped_raises_error():
    """
    Test that cascade_delete=True with scoped_cleanup=False raises a ValueError.
    Cascade delete only makes sense with scoped cleanup where parent nodes own children.
    """
    with pytest.raises(ValueError) as excinfo:
        build_cleanup_queries(UnscopedNodeSchema(), cascade_delete=True)

    assert "cascade_delete=True requires scoped_cleanup=True" in str(excinfo.value)
    assert "UnscopedNode" in str(excinfo.value)
