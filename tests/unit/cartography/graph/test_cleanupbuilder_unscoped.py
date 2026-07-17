from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.querybuilder import _get_module_from_schema
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.github.dependencies import GitHubDependencySchema
from cartography.version import get_cartography_version
from tests.data.graph.querybuilder.sample_models.allow_unscoped import (
    UnscopedNodeSchema,
)
from tests.data.graph.querybuilder.sample_models.allow_unscoped import (
    UnscopedNodeWithExtraLabelsSchema,
)
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


def test_unscoped_node_sanity_checks():
    """
    Test creating an unscoped node schema and ensure that the optional attributes are set correctly.
    """
    schema: UnscopedNodeSchema = UnscopedNodeSchema()
    assert schema.extra_node_labels is None
    assert schema.scoped_cleanup is False
    assert schema.sub_resource_relationship is None

    assert schema.other_relationships is not None
    assert len(schema.other_relationships.rels) == 1
    assert schema.other_relationships.rels[0].target_node_label == "SimpleNode"


def test_build_ingestion_query_unscoped():
    """
    Test creating a query for an unscoped node schema.
    """
    module_version = get_cartography_version()
    module_name = _get_module_from_schema(UnscopedNodeSchema())

    # Act
    query = build_ingestion_query(UnscopedNodeSchema())

    expected = f"""
        UNWIND $DictList AS item
            MERGE (i:UnscopedNode{{id: item.id}})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i._module_name = "{module_name}",
                i._module_version = "{module_version}",
                i.lastupdated = $lastupdated,
                i.name = item.name

            WITH i, item
            CALL (i, item) {{
                OPTIONAL MATCH (n0:SimpleNode)
                WHERE
                    n0.id = item.simple_node_id
                WITH i, item, n0 WHERE n0 IS NOT NULL
                MERGE (i)-[r0:RELATES_TO]->(n0)
                ON CREATE SET r0.firstseen = timestamp()
                SET
                    r0._module_name = "{module_name}",
                    r0._module_version = "{module_version}",
                    r0.lastupdated = $lastupdated
            }}
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query


def test_build_cleanup_queries_unscoped():
    """
    Test creating cleanup queries for an unscoped node schema.e
    Since allow_unscoped_cleanup is True, it should clean up both nodes and relationships.
    """
    # Act
    queries = build_cleanup_queries(UnscopedNodeSchema())

    actual_delete_node = remove_leading_whitespace_and_empty_lines(queries[0])
    expected_delete_node = """
        MATCH (n:UnscopedNode)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """

    actual_delete_rel = remove_leading_whitespace_and_empty_lines(queries[1])
    expected_delete_rel = """
        MATCH (n:UnscopedNode)
        MATCH (n)-[r:RELATES_TO]->(:SimpleNode)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """

    # Assert
    assert actual_delete_node == remove_leading_whitespace_and_empty_lines(
        expected_delete_node
    )
    assert actual_delete_rel == remove_leading_whitespace_and_empty_lines(
        expected_delete_rel
    )


def test_build_cleanup_queries_unscoped_includes_unconditional_extra_labels():
    """
    Unscoped cleanup deletes every stale node its MATCH statement touches, so
    the MATCH must be constrained to all of the schema's unconditional labels:
    canonical labels like `Dependency` are shared across modules, and matching
    on the primary label alone lets one module delete another module's nodes
    that carry the shared label as an extra label (issue #3035).
    Conditional labels are only present on some nodes of the schema, so they
    must NOT be part of the MATCH or stale nodes without them would leak.
    """
    # Act
    queries = build_cleanup_queries(UnscopedNodeWithExtraLabelsSchema())

    actual_delete_node = remove_leading_whitespace_and_empty_lines(queries[0])
    expected_delete_node = """
        MATCH (n:SharedCanonicalNode:UnscopedOwnedNode)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """

    actual_delete_rel = remove_leading_whitespace_and_empty_lines(queries[1])
    expected_delete_rel = """
        MATCH (n:SharedCanonicalNode:UnscopedOwnedNode)
        MATCH (n)-[r:RELATES_TO]->(:SimpleNode)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """

    # Assert: the conditional label is excluded, the unconditional one is not.
    assert actual_delete_node == remove_leading_whitespace_and_empty_lines(
        expected_delete_node
    )
    assert actual_delete_rel == remove_leading_whitespace_and_empty_lines(
        expected_delete_rel
    )
    for query in queries:
        assert "Critical" not in query


def test_build_cleanup_queries_unscoped_github_dependency_spares_other_modules():
    """
    Regression test for issue #3035: GitHub's unscoped Dependency cleanup used
    to MATCH on the shared canonical `Dependency` label alone, which deleted
    Semgrep and Socket dependency nodes that carry `Dependency` as an extra
    label. The MATCH must also require GitHub's own `GitHubDependency` label so
    that the cleanup only ever touches nodes that the GitHub module ingested.
    """
    # Act
    queries = build_cleanup_queries(GitHubDependencySchema())

    # Assert
    actual_delete_node = remove_leading_whitespace_and_empty_lines(queries[0])
    expected_delete_node = """
        MATCH (n:Dependency:GitHubDependency)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert actual_delete_node == remove_leading_whitespace_and_empty_lines(
        expected_delete_node
    )
    # Every cleanup query for this schema, including the relationship ones,
    # must be constrained to nodes owned by the GitHub module.
    for query in queries:
        assert "(n:Dependency:GitHubDependency)" in query
