"""Exercise permission property clearing through the real workflow loader."""

from cartography.intel.github.actions import enrich_workflow_with_parsed_content
from cartography.intel.github.actions import load_workflows
from cartography.intel.github.actions import transform_workflows
from cartography.intel.github.workflow_parser import parse_workflow_yaml
from tests.data.github.actions import GET_REPO_WORKFLOWS
from tests.integration.util import check_nodes


def test_permission_property_cleared_when_declaration_becomes_unknown(neo4j_session):
    # Arrange: seed a declared value through the real loader on a fresh graph.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "CREATE (:GitHubOrganization {id: 'https://github.com/simpsoncorp'}) "
        "CREATE (:GitHubRepository {id: 'https://github.com/simpsoncorp/sample_repo'})"
    )
    workflow = transform_workflows(
        [GET_REPO_WORKFLOWS[0]], "simpsoncorp", "sample_repo"
    )[0]
    declared = enrich_workflow_with_parsed_content(
        workflow,
        parse_workflow_yaml("jobs: {deploy: {permissions: {contents: write}}}"),
        "simpsoncorp",
        "sample_repo",
    )
    load_workflows(neo4j_session, [declared], 1, "https://github.com/simpsoncorp")
    assert check_nodes(
        neo4j_session, "GitHubWorkflow", ["id", "permissions_contents"]
    ) == {(12345678, "write")}
    unknown = enrich_workflow_with_parsed_content(
        workflow,
        parse_workflow_yaml("jobs: {deploy: {}}"),
        "simpsoncorp",
        "sample_repo",
    )

    # Act
    load_workflows(neo4j_session, [unknown], 2, "https://github.com/simpsoncorp")

    # Assert: the old value is removed, rather than retained as stale access.
    assert check_nodes(
        neo4j_session,
        "GitHubWorkflow",
        ["id", "permissions_contents", "lastupdated"],
    ) == {(12345678, None, 2)}
