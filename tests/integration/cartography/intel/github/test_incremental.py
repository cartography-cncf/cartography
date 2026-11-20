from cartography.intel.github import repos
from cartography.intel.github import supply_chain
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

ORG_URL = "https://github.com/incremental-test"
ARCHIVED_URL = f"{ORG_URL}/archived"
ACTIVE_URL = f"{ORG_URL}/active"


def test_archived_ruleset_preservation_does_not_keep_stale_active_repo_edges(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (org:GitHubOrganization {id: $org_url})
        CREATE (archived:GitHubRepository {id: $archived_url})
        CREATE (active:GitHubRepository {id: $active_url})
        CREATE (ruleset:GitHubRuleset {id: 'shared', lastupdated: 1})
        CREATE (rule:GitHubRulesetRule {id: 'rule', lastupdated: 1})
        CREATE (archived)-[:HAS_RULESET {lastupdated: 1}]->(ruleset)
        CREATE (active)-[:HAS_RULESET {lastupdated: 1}]->(ruleset)
        CREATE (ruleset)-[:CONTAINS_RULE {lastupdated: 1}]->(rule)
        CREATE (org)-[:RESOURCE {lastupdated: 1}]->(ruleset)
        CREATE (org)-[:RESOURCE {lastupdated: 1}]->(rule)
        """,
        org_url=ORG_URL,
        archived_url=ARCHIVED_URL,
        active_url=ACTIVE_URL,
    )

    # Act
    repos._touch_archived_repo_details(neo4j_session, {ARCHIVED_URL}, 2, ORG_URL)
    repos.cleanup_rulesets(neo4j_session, {"UPDATE_TAG": 2}, ORG_URL)

    # Assert
    assert check_nodes(neo4j_session, "GitHubRulesetRule", ["id", "lastupdated"]) == {
        ("rule", 2),
    }
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubRuleset",
        "id",
        "HAS_RULESET",
    ) == {(ARCHIVED_URL, "shared")}
    assert check_rels(
        neo4j_session,
        "GitHubRuleset",
        "id",
        "GitHubRulesetRule",
        "id",
        "CONTAINS_RULE",
    ) == {("shared", "rule")}


def test_supply_chain_preserves_archived_links_without_creating_new_matches(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (org:GitHubOrganization {id: $org_url})
        CREATE (repo:GitHubRepository {id: $repo_url})
        CREATE (workflow:GitHubWorkflow {id: 1, repo_url: $repo_url, path: 'ci.yml'})
        CREATE (repo)-[:HAS_WORKFLOW]->(workflow)
        CREATE (package:GitHubPackage {id: 'package'})
        CREATE (repo)-[:HAS_PACKAGE]->(package)
        CREATE (old:GitHubContainerImage:Image {
            id: 'old', digest: 'sha256:old', source_uri: $repo_url
        })
        CREATE (new:GitHubContainerImage:Image {
            id: 'new', digest: 'sha256:new', source_uri: $repo_url
        })
        CREATE (org)-[:RESOURCE]->(old)
        CREATE (org)-[:RESOURCE]->(new)
        CREATE (package)-[:HAS_IMAGE]->(new)
        CREATE (old)-[:PACKAGED_FROM {
            lastupdated: 1,
            _sub_resource_label: 'GitHubOrganization',
            _sub_resource_id: 'incremental-test'
        }]->(repo)
        CREATE (old)-[:PACKAGED_BY {
            lastupdated: 1,
            _sub_resource_label: 'GitHubOrganization',
            _sub_resource_id: 'incremental-test'
        }]->(workflow)
        """,
        org_url=ORG_URL,
        repo_url=ARCHIVED_URL,
    )

    # Act
    supply_chain.sync(
        neo4j_session,
        "token",
        "https://api.github.com/graphql",
        "incremental-test",
        2,
        {"UPDATE_TAG": 2},
        [{"url": ARCHIVED_URL}],
        workflows=[{"repo_url": ARCHIVED_URL, "path": "ci.yml"}],
        excluded_repo_urls={ARCHIVED_URL},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "Image",
        "id",
        "GitHubRepository",
        "id",
        "PACKAGED_FROM",
    ) == {("old", ARCHIVED_URL)}
    assert check_rels(
        neo4j_session,
        "Image",
        "id",
        "GitHubWorkflow",
        "id",
        "PACKAGED_BY",
    ) == {("old", 1)}
