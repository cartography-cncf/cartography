"""Exercise declared-permission updates through the real workflow loader."""

import yaml

from cartography.intel.github.actions import enrich_workflow_with_parsed_content
from cartography.intel.github.actions import load_workflows
from cartography.intel.github.actions import transform_workflows
from cartography.intel.github.workflow_parser import parse_workflow_yaml
from tests.data.github.actions import GET_REPO_WORKFLOWS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_permission_summary_order_and_property_updates(neo4j_session):
    # Arrange: this split-ingestion test targets loader updates, including null removal.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "CREATE (:GitHubOrganization {id: 'https://github.com/simpsoncorp'}) "
        "CREATE (:GitHubRepository {id: 'https://github.com/simpsoncorp/sample_repo'})"
    )
    workflow = transform_workflows(
        [GET_REPO_WORKFLOWS[0]], "simpsoncorp", "sample_repo"
    )[0]
    jobs = {
        "check": {"permissions": {"contents": "read"}},
        "release": {"permissions": {"contents": "write", "id-token": "write"}},
    }
    snapshots = [
        ({"jobs": jobs}, "write", "write"),
        ({"jobs": dict(reversed(list(jobs.items())))}, "write", "write"),
        (
            {
                "permissions": {"contents": "write"},
                "jobs": {"check": {"permissions": {}}},
            },
            "none",
            "none",
        ),
        ({"jobs": {"check": {}}}, None, None),
    ]
    enriched = [
        (
            enrich_workflow_with_parsed_content(
                workflow,
                parse_workflow_yaml(yaml.safe_dump(data, sort_keys=False)),
                "simpsoncorp",
                "sample_repo",
            ),
            contents,
            id_token,
        )
        for data, contents, id_token in snapshots
    ]

    for update_tag, (data, contents, id_token) in enumerate(enriched, start=1):
        # Act
        load_workflows(
            neo4j_session, [data], update_tag, "https://github.com/simpsoncorp"
        )

        # Assert: stable identity, values, relationships and refreshed ingestion tag.
        assert check_nodes(
            neo4j_session,
            "GitHubWorkflow",
            ["id", "permissions_contents", "permissions_id_token", "lastupdated"],
        ) == {(12345678, contents, id_token, update_tag)}
        assert check_rels(
            neo4j_session,
            "GitHubRepository",
            "id",
            "GitHubWorkflow",
            "id",
            "HAS_WORKFLOW",
        ) == {("https://github.com/simpsoncorp/sample_repo", 12345678)}
        assert check_rels(
            neo4j_session,
            "GitHubOrganization",
            "id",
            "GitHubWorkflow",
            "id",
            "RESOURCE",
        ) == {("https://github.com/simpsoncorp", 12345678)}
