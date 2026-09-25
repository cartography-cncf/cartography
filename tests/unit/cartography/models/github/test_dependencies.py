from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.models.extra_labels import DEPENDENCY
from cartography.models.github.dependencies import GitHubDependencySchema
from tests.unit.cartography.graph.helpers import (
    remove_leading_whitespace_and_empty_lines,
)


def test_github_dependency_labels():
    """
    GitHubDependency must be the primary label and Dependency a shared extra
    label. Regression guard for #3035: if Dependency were the primary label,
    github's unscoped cleanup would delete Semgrep/SocketDev Dependency nodes.
    """
    schema = GitHubDependencySchema()
    assert schema.label == "GitHubDependency"
    assert schema.extra_node_labels is not None
    assert schema.extra_node_labels.labels == (DEPENDENCY,)
    # Unscoped by design: the node is globally shared across orgs.
    assert schema.scoped_cleanup is False
    assert schema.sub_resource_relationship is None


def test_github_dependency_cleanup_scoped_to_own_label():
    """
    The detach and node-delete queries must MATCH on GitHubDependency, not the
    shared Dependency label, so github only reaps nodes (and their relationships)
    it ingested itself (#3035).
    """
    queries = build_cleanup_queries(GitHubDependencySchema())
    detach_query, node_delete_query = queries[0], queries[1]

    actual_detach = remove_leading_whitespace_and_empty_lines(detach_query)
    expected_detach = """
        MATCH (n:GitHubDependency)
        WHERE n.lastupdated <> $UPDATE_TAG
        MATCH (n)-[r]-()
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """
    assert actual_detach == remove_leading_whitespace_and_empty_lines(expected_detach)
    assert "MATCH (n:Dependency)" not in detach_query

    actual_node_delete = remove_leading_whitespace_and_empty_lines(node_delete_query)
    expected_node_delete = """
        MATCH (n:GitHubDependency)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert actual_node_delete == remove_leading_whitespace_and_empty_lines(
        expected_node_delete
    )
    assert "MATCH (n:Dependency)" not in node_delete_query
