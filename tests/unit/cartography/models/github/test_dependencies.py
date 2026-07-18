from cartography.graph.cleanupbuilder import build_cleanup_queries
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
    assert schema.extra_node_labels.labels == ["Dependency"]
    # Unscoped by design: the node is globally shared across orgs.
    assert schema.scoped_cleanup is False
    assert schema.sub_resource_relationship is None


def test_github_dependency_cleanup_scoped_to_own_label():
    """
    The node-delete query must MATCH on GitHubDependency, not the shared
    Dependency label, so github only reaps nodes it ingested itself (#3035).
    """
    node_delete_query = build_cleanup_queries(GitHubDependencySchema())[0]
    actual = remove_leading_whitespace_and_empty_lines(node_delete_query)

    expected = """
        MATCH (n:GitHubDependency)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert actual == remove_leading_whitespace_and_empty_lines(expected)
    assert "MATCH (n:Dependency)" not in node_delete_query
