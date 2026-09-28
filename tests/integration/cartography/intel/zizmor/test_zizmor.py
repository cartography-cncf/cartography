import pytest

import cartography.intel.zizmor
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REPO_URL = "https://github.com/simpsoncorp/sample_repo"
OTHER_REPO_URL = "https://github.com/different-org/different-repo"
MAPPING_SOURCE = "tests/data/zizmor/repository_mappings.yaml"
SINGLE_REPO_MAPPING_SOURCE = "tests/data/zizmor/repository_mappings_single_repo.yaml"
PARTIAL_FAILURE_MAPPING_SOURCE = (
    "tests/data/zizmor/repository_mappings_partial_failure.yaml"
)
STDIN_MAPPING_SOURCE = "tests/data/zizmor/repository_mappings_stdin.yaml"
DUPLICATE_URL_MAPPING_SOURCE = (
    "tests/data/zizmor/repository_mappings_duplicate_url.yaml"
)


def _ensure_github_data_exists(neo4j_session):
    """
    Create the GitHub nodes that zizmor findings attach to.

    Zizmor runs after the GitHub module, which is what normally creates these.
    """
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        SET org.username = "simpsoncorp"

        MERGE (repo:GitHubRepository{id: $repo_url})
        SET repo.name = "sample_repo"
        MERGE (repo)-[:OWNER]->(org)

        MERGE (ci:GitHubWorkflow{id: 12345678})
        SET ci.name = "CI", ci.path = ".github/workflows/ci.yml", ci.repo_url = $repo_url
        MERGE (repo)-[:HAS_WORKFLOW]->(ci)

        MERGE (deploy:GitHubWorkflow{id: 12345679})
        SET deploy.name = "Deploy",
            deploy.path = ".github/workflows/deploy.yml",
            deploy.repo_url = $repo_url
        MERGE (repo)-[:HAS_WORKFLOW]->(deploy)

        MERGE (checkout:GitHubAction{id: "simpsoncorp:actions/checkout@v4"})
        SET checkout.full_name = "actions/checkout@v4", checkout.is_pinned = false
        MERGE (ci)-[:USES_ACTION]->(checkout)

        MERGE (pinned:GitHubAction{id: "simpsoncorp:actions/setup-node@0000000000000000000000000000000000000000"})
        SET pinned.full_name = "actions/setup-node@0000000000000000000000000000000000000000",
            pinned.is_pinned = true
        MERGE (deploy)-[:USES_ACTION]->(pinned)

        MERGE (local:GitHubAction{id: "simpsoncorp/sample_repo:./.github/actions/build"})
        SET local.full_name = "./.github/actions/build", local.is_local = true
        MERGE (ci)-[:USES_ACTION]->(local)
        """,
        repo_url=TEST_REPO_URL,
    )


def _cleanup_zizmor_data(neo4j_session):
    neo4j_session.run("MATCH (n:ZizmorFinding) DETACH DELETE n")


def test_sync_zizmor_findings(neo4j_session):
    # Arrange
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)

    # Act
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        SINGLE_REPO_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert - findings are created with their determinations normalized
    assert check_nodes(
        neo4j_session,
        "ZizmorFinding",
        ["audit_id", "severity", "confidence", "persona", "ignored", "file_path"],
    ) == {
        (
            "template-injection",
            "high",
            "high",
            "regular",
            False,
            ".github/workflows/ci.yml",
        ),
        ("unpinned-uses", "high", "high", "regular", False, ".github/workflows/ci.yml"),
        (
            "excessive-permissions",
            "medium",
            "high",
            "regular",
            True,
            ".github/workflows/deploy.yml",
        ),
        (
            "impostor-commit",
            "high",
            "high",
            "regular",
            False,
            ".github/workflows/deploy.yml",
        ),
    }

    # Assert - the SecurityIssue ontology label is applied
    assert (
        neo4j_session.run(
            "MATCH (n:ZizmorFinding) WHERE NOT n:SecurityIssue RETURN count(n) AS c"
        ).single()["c"]
        == 0
    )


def test_sync_zizmor_findings_attaches_to_github_nodes(neo4j_session):
    # Arrange
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)

    # Act
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        SINGLE_REPO_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert - every finding is linked to the workflow it was found in
    assert check_rels(
        neo4j_session,
        "ZizmorFinding",
        "audit_id",
        "GitHubWorkflow",
        "path",
        "AFFECTS",
    ) == {
        ("template-injection", ".github/workflows/ci.yml"),
        ("unpinned-uses", ".github/workflows/ci.yml"),
        ("excessive-permissions", ".github/workflows/deploy.yml"),
        ("impostor-commit", ".github/workflows/deploy.yml"),
    }

    # Assert - only findings located on a `uses` key resolve to an action
    assert check_rels(
        neo4j_session,
        "ZizmorFinding",
        "audit_id",
        "GitHubAction",
        "id",
        "AFFECTS",
    ) == {
        ("unpinned-uses", "simpsoncorp:actions/checkout@v4"),
        ("unpinned-uses", "simpsoncorp/sample_repo:./.github/actions/build"),
        (
            "impostor-commit",
            "simpsoncorp:actions/setup-node@0000000000000000000000000000000000000000",
        ),
    }

    # Assert - every finding is linked to its repository
    assert check_rels(
        neo4j_session,
        "ZizmorFinding",
        "audit_id",
        "GitHubRepository",
        "id",
        "FOUND_IN",
    ) == {
        ("template-injection", TEST_REPO_URL),
        ("unpinned-uses", TEST_REPO_URL),
        ("excessive-permissions", TEST_REPO_URL),
        ("impostor-commit", TEST_REPO_URL),
    }


def test_sync_zizmor_findings_cleans_up_stale_findings(neo4j_session):
    # Arrange - a previous sync left a finding behind that is no longer reported
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (n:ZizmorFinding{id: "zizmor-stale"})
        SET n.audit_id = "artipacked",
            n.repository_url = $repo_url,
            n.lastupdated = $old_tag
        """,
        repo_url=TEST_REPO_URL,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        SINGLE_REPO_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert "artipacked" not in {
        audit_id
        for (audit_id,) in check_nodes(neo4j_session, "ZizmorFinding", ["audit_id"])
    }


def test_sync_zizmor_findings_skips_cleanup_for_partially_read_repository(
    neo4j_session,
):
    """
    A repository whose reports could not all be read keeps its existing findings,
    so that an unreadable report never silently empties the graph.
    """
    # Arrange
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (n:ZizmorFinding{id: "zizmor-stale"})
        SET n.audit_id = "artipacked",
            n.repository_url = $repo_url,
            n.lastupdated = $old_tag
        """,
        repo_url=TEST_REPO_URL,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act - the mapping lists one readable report and one that does not exist
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        PARTIAL_FAILURE_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "ZizmorFinding", ["audit_id"]) == {
        ("artipacked",)
    }


def test_sync_zizmor_findings_removes_stale_action_relationships(neo4j_session):
    """
    A finding id does not cover its `uses` reference, so bumping an action leaves
    the finding node in place while its AFFECTS edge must move to the new action.
    The edge to the old action has to go with it.
    """
    # Arrange - a previous sync linked the finding to an older action version
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (old:GitHubAction{id: "simpsoncorp:actions/checkout@v3"})
        SET old.full_name = "actions/checkout@v3", old.lastupdated = $old_tag
        """,
        old_tag=TEST_UPDATE_TAG - 1,
    )
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        SINGLE_REPO_MAPPING_SOURCE,
        TEST_UPDATE_TAG - 1,
    )
    neo4j_session.run(
        """
        MATCH (f:ZizmorFinding{audit_id: "unpinned-uses"})
        MATCH (old:GitHubAction{id: "simpsoncorp:actions/checkout@v3"})
        MERGE (f)-[r:AFFECTS]->(old)
        SET r.lastupdated = $old_tag
        """,
        old_tag=TEST_UPDATE_TAG - 1,
    )
    assert ("simpsoncorp:actions/checkout@v3",) in {
        (action_id,)
        for (_, action_id) in check_rels(
            neo4j_session,
            "ZizmorFinding",
            "audit_id",
            "GitHubAction",
            "id",
            "AFFECTS",
        )
    }

    # Act - the same reports are synced again under a new update tag
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        SINGLE_REPO_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert - the stale edge is gone while the finding and its current edges remain
    assert check_rels(
        neo4j_session,
        "ZizmorFinding",
        "audit_id",
        "GitHubAction",
        "id",
        "AFFECTS",
    ) == {
        ("unpinned-uses", "simpsoncorp:actions/checkout@v4"),
        ("unpinned-uses", "simpsoncorp/sample_repo:./.github/actions/build"),
        (
            "impostor-commit",
            "simpsoncorp:actions/setup-node@0000000000000000000000000000000000000000",
        ),
    }


def test_sync_zizmor_findings_skips_cleanup_when_a_finding_cannot_be_joined(
    neo4j_session,
):
    """
    A finding read from stdin is well-formed but has no path to join on. It is
    still an open finding, so cleanup must not run and delete the rest.
    """
    # Arrange
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (n:ZizmorFinding{id: "zizmor-stale"})
        SET n.audit_id = "artipacked",
            n.repository_url = $repo_url,
            n.lastupdated = $old_tag
        """,
        repo_url=TEST_REPO_URL,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        STDIN_MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert - the unjoinable finding blocked cleanup, so the stale one survives
    assert ("artipacked",) in check_nodes(neo4j_session, "ZizmorFinding", ["audit_id"])


def test_sync_zizmor_findings_refuses_a_mapping_with_duplicate_repository_urls(
    neo4j_session,
):
    """
    Two entries for one repository would let a fully read entry authorize cleanup
    for the repository while a second entry for it failed, deleting findings the
    failed entry would have reported. The mapping is rejected before any write.
    """
    # Arrange
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (n:ZizmorFinding{id: "zizmor-stale"})
        SET n.audit_id = "artipacked",
            n.repository_url = $repo_url,
            n.lastupdated = $old_tag
        """,
        repo_url=TEST_REPO_URL,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act - the second entry for this repository lists an unreadable report
    with pytest.raises(ValueError, match="Each repository may only appear once"):
        cartography.intel.zizmor.sync_zizmor_findings(
            neo4j_session,
            DUPLICATE_URL_MAPPING_SOURCE,
            TEST_UPDATE_TAG,
        )

    # Assert - nothing was written and nothing was deleted
    assert check_nodes(neo4j_session, "ZizmorFinding", ["audit_id"]) == {
        ("artipacked",)
    }


def test_sync_zizmor_findings_isolates_cleanup_per_repository(neo4j_session):
    """
    One repository failing must not stop stale findings from being cleaned up in
    the repositories that were read successfully.
    """
    # Arrange - both repos hold a stale finding; only the second repo's mapping
    # entry lists an unreadable report.
    _cleanup_zizmor_data(neo4j_session)
    _ensure_github_data_exists(neo4j_session)
    neo4j_session.run(
        """
        MERGE (a:ZizmorFinding{id: "zizmor-stale-a"})
        SET a.audit_id = "artipacked",
            a.repository_url = $repo_url,
            a.lastupdated = $old_tag

        MERGE (b:ZizmorFinding{id: "zizmor-stale-b"})
        SET b.audit_id = "self-hosted-runner",
            b.repository_url = $other_repo_url,
            b.lastupdated = $old_tag
        """,
        repo_url=TEST_REPO_URL,
        other_repo_url=OTHER_REPO_URL,
        old_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    cartography.intel.zizmor.sync_zizmor_findings(
        neo4j_session,
        MAPPING_SOURCE,
        TEST_UPDATE_TAG,
    )

    # Assert - the fully observed repo lost its stale finding, the other kept it
    surviving_stale = {
        (audit_id, repository_url)
        for (audit_id, repository_url) in check_nodes(
            neo4j_session,
            "ZizmorFinding",
            ["audit_id", "repository_url"],
        )
        if audit_id in {"artipacked", "self-hosted-runner"}
    }
    assert surviving_stale == {("self-hosted-runner", OTHER_REPO_URL)}
