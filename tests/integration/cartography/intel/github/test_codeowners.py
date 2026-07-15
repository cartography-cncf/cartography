from unittest.mock import patch

import cartography.intel.github.codeowners
from cartography.intel.github.codeowners import CodeOwnersFileFetchResult
from cartography.intel.github.codeowners import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_GITHUB_ORG = "codeownercorp"
TEST_GITHUB_ORG_URL = "https://github.com/codeownercorp"
TEST_REPO_URL = "https://github.com/codeownercorp/sample_repo"
TEST_API_KEY = "token"


def _repository_rows() -> list[dict]:
    return [
        {
            "id": TEST_REPO_URL,
            "name": "sample_repo",
            "defaultbranch": "main",
            "owner_org_id": TEST_GITHUB_ORG_URL,
        },
    ]


def _manifest_rows() -> list[dict]:
    return [
        {
            "id": f"{TEST_REPO_URL}#/package.json",
            "repo_url": TEST_REPO_URL,
            "repo_relative_path": "package.json",
            "blob_path": "/package.json",
        },
        {
            "id": f"{TEST_REPO_URL}#/src/index.js",
            "repo_url": TEST_REPO_URL,
            "repo_relative_path": "src/index.js",
            "blob_path": "/src/index.js",
        },
    ]


def _seed_codeowners_prerequisites(neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization {id: $org_url})
        SET org.username = $org

        MERGE (repo:GitHubRepository {id: $repo_url})
        SET repo.url = $repo_url,
            repo.name = "sample_repo",
            repo.defaultbranch = "main"
        MERGE (repo)-[:OWNER {lastupdated: $update_tag}]->(org)

        MERGE (team:GitHubTeam {id: $team_url})
        SET team.url = $team_url,
            team.name = "security"
        MERGE (org)-[:RESOURCE {lastupdated: $update_tag}]->(team)

        MERGE (user:GitHubUser {id: $user_url})
        SET user.username = "js-owner"

        MERGE (mixed_case_user:GitHubUser {id: $mixed_case_user_url})
        SET mixed_case_user.username = "MixedCaseUser"

        MERGE (package_manifest:GitHubDependencyGraphManifest {id: $package_manifest_id})
        SET package_manifest.blob_path = "/package.json",
            package_manifest.repo_relative_path = "package.json",
            package_manifest.filename = "package.json",
            package_manifest.repo_url = $repo_url
        MERGE (org)-[:RESOURCE {lastupdated: $update_tag}]->(package_manifest)
        MERGE (repo)-[:HAS_MANIFEST {lastupdated: $update_tag}]->(package_manifest)

        MERGE (js_manifest:GitHubDependencyGraphManifest {id: $js_manifest_id})
        SET js_manifest.blob_path = "/src/index.js",
            js_manifest.repo_relative_path = "src/index.js",
            js_manifest.filename = "index.js",
            js_manifest.repo_url = $repo_url
        MERGE (org)-[:RESOURCE {lastupdated: $update_tag}]->(js_manifest)
        MERGE (repo)-[:HAS_MANIFEST {lastupdated: $update_tag}]->(js_manifest)
        """,
        org=TEST_GITHUB_ORG,
        org_url=TEST_GITHUB_ORG_URL,
        repo_url=TEST_REPO_URL,
        team_url=f"https://github.com/orgs/{TEST_GITHUB_ORG}/teams/security",
        user_url="https://github.com/js-owner",
        mixed_case_user_url="https://github.com/MixedCaseUser",
        package_manifest_id=f"{TEST_REPO_URL}#/package.json",
        js_manifest_id=f"{TEST_REPO_URL}#/src/index.js",
        update_tag=TEST_UPDATE_TAG,
    )


def _run_codeowners_sync(
    neo4j_session,
    update_tag: int,
    dependency_manifests_cleanup_safe: bool = True,
    manifests: list[dict] | None = None,
) -> None:
    sync(
        neo4j_session,
        {"UPDATE_TAG": update_tag},
        TEST_API_KEY,
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
        _repository_rows(),
        _manifest_rows() if manifests is None else manifests,
        dependency_manifests_cleanup_safe=dependency_manifests_cleanup_safe,
        github_users=[
            {"login": "js-owner", "url": "https://github.com/js-owner"},
            {"login": "MixedCaseUser", "url": "https://github.com/MixedCaseUser"},
        ],
        github_teams=[
            {
                "org_login": TEST_GITHUB_ORG,
                "name": "security",
                "url": f"https://github.com/orgs/{TEST_GITHUB_ORG}/teams/security",
            },
        ],
    )


def test_sync_codeowners_loads_rules_owner_relationships_and_manifest_matches(
    neo4j_session,
) -> None:
    # Arrange
    _seed_codeowners_prerequisites(neo4j_session)
    content = """
    * @global-owner
    /package.json @CodeOwnerCorp/Security
    src/*.js @JS-Owner @mixedcaseuser
    docs/ docs@example.com
    """

    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", content, True),
    ):
        # Act
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "GitHubCodeOwnerRule", ["pattern"]) == {
        ("*",),
        ("/package.json",),
        ("src/*.js",),
        ("docs/",),
    }
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "id",
        "GitHubCodeOwnerRule",
        "pattern",
        "HAS_CODEOWNER_RULE",
    ) == {
        (TEST_REPO_URL, "*"),
        (TEST_REPO_URL, "/package.json"),
        (TEST_REPO_URL, "src/*.js"),
        (TEST_REPO_URL, "docs/"),
    }
    assert check_rels(
        neo4j_session,
        "GitHubCodeOwnerRule",
        "pattern",
        "GitHubTeam",
        "id",
        "CODEOWNER",
    ) == {
        (
            "/package.json",
            f"https://github.com/orgs/{TEST_GITHUB_ORG}/teams/security",
        ),
    }
    assert check_rels(
        neo4j_session,
        "GitHubCodeOwnerRule",
        "pattern",
        "GitHubUser",
        "id",
        "CODEOWNER",
    ) == {
        ("src/*.js", "https://github.com/MixedCaseUser"),
        ("src/*.js", "https://github.com/js-owner"),
    }

    matched_manifests = neo4j_session.run(
        """
        MATCH (m:GitHubDependencyGraphManifest)-[r:MATCHES_CODEOWNER_RULE]->(rule:GitHubCodeOwnerRule)
        RETURN m.repo_relative_path AS manifest_path,
               rule.pattern AS pattern,
               r.match_pattern AS match_pattern,
               r.matched_path AS matched_path
        ORDER BY manifest_path
        """
    )
    assert {
        (
            row["manifest_path"],
            row["pattern"],
            row["match_pattern"],
            row["matched_path"],
        )
        for row in matched_manifests
    } == {
        ("package.json", "/package.json", "/package.json", "package.json"),
        ("src/index.js", "src/*.js", "src/*.js", "src/index.js"),
    }


def test_sync_codeowners_successful_resync_cleans_stale_rules_and_matches(
    neo4j_session,
) -> None:
    # Arrange
    _seed_codeowners_prerequisites(neo4j_session)
    first_content = """
    * @global-owner
    /package.json @codeownercorp/security
    """
    second_content = "README.md @codeownercorp/security"

    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", first_content, True),
    ):
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG)

    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", second_content, True),
    ):
        # Act
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG_2)

    # Assert
    assert check_nodes(neo4j_session, "GitHubCodeOwnerRule", ["pattern"]) == {
        ("README.md",),
    }
    stale_match_count = neo4j_session.run(
        """
        MATCH (:GitHubDependencyGraphManifest)-[r:MATCHES_CODEOWNER_RULE]->(:GitHubCodeOwnerRule)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert stale_match_count == 0


def test_sync_codeowners_fetch_failure_preserves_existing_rules(
    neo4j_session,
) -> None:
    # Arrange
    _seed_codeowners_prerequisites(neo4j_session)
    content = "/package.json @codeownercorp/security"
    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", content, True),
    ):
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG)

    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult(None, None, False),
    ):
        # Act
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG_2)

    # Assert
    rows = neo4j_session.run(
        """
        MATCH (rule:GitHubCodeOwnerRule)
        RETURN rule.pattern AS pattern, rule.lastupdated AS lastupdated
        """
    )
    assert {(row["pattern"], row["lastupdated"]) for row in rows} == {
        ("/package.json", TEST_UPDATE_TAG),
    }


def test_sync_codeowners_preserves_manifest_matches_when_manifest_fetch_incomplete(
    neo4j_session,
) -> None:
    # Arrange
    _seed_codeowners_prerequisites(neo4j_session)
    content = "/package.json @codeownercorp/security"
    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", content, True),
    ):
        _run_codeowners_sync(neo4j_session, TEST_UPDATE_TAG)

    with patch.object(
        cartography.intel.github.codeowners,
        "get_effective_codeowners_file",
        return_value=CodeOwnersFileFetchResult("CODEOWNERS", content, True),
    ):
        # Act
        _run_codeowners_sync(
            neo4j_session,
            TEST_UPDATE_TAG_2,
            dependency_manifests_cleanup_safe=False,
            manifests=[],
        )

    # Assert
    rows = neo4j_session.run(
        """
        MATCH (m:GitHubDependencyGraphManifest)-[r:MATCHES_CODEOWNER_RULE]->(rule:GitHubCodeOwnerRule)
        RETURN m.repo_relative_path AS manifest_path,
               rule.pattern AS pattern,
               r.lastupdated AS lastupdated
        """
    )
    assert {
        (row["manifest_path"], row["pattern"], row["lastupdated"]) for row in rows
    } == {
        ("package.json", "/package.json", TEST_UPDATE_TAG),
    }
