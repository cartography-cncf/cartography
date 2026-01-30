"""
Integration tests for GitLab cascade_delete cleanup behavior.

These tests verify that when parent nodes (Projects) are deleted,
their child nodes are also deleted via cascade_delete to prevent orphaned nodes.

This addresses the scenario where a GitLab project is deleted between syncs -
without cascade_delete, the project's resources (branches, dependency files, etc.)
would remain as orphans since resource cleanup is scoped to project_url.
"""

from cartography.graph.job import GraphJob
from cartography.models.gitlab.projects import GitLabProjectSchema
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790
TEST_ORG_URL = "https://gitlab.example.com/myorg"
TEST_PROJECT_URL = "https://gitlab.example.com/myorg/test-project"


class TestProjectCascadeDelete:
    """
    Test that cascade_delete on GitLabProject cleanup removes orphaned child resources.
    """

    def test_project_cascade_deletes_child_branches(self, neo4j_session):
        """
        When a stale GitLabProject is deleted with cascade_delete=True,
        its child branches should also be deleted.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create organization
        neo4j_session.run(
            """
            MERGE (o:GitLabOrganization {id: $org_url})
            SET o.lastupdated = $tag
            """,
            org_url=TEST_ORG_URL,
            tag=TEST_UPDATE_TAG_V2,  # Current tag - org is fresh
        )

        # Create stale project (old update tag)
        neo4j_session.run(
            """
            MERGE (p:GitLabProject {id: $project_url})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GitLabOrganization {id: $org_url})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_url=TEST_PROJECT_URL,
            org_url=TEST_ORG_URL,
            old_tag=TEST_UPDATE_TAG,  # Old tag - project is stale
        )

        # Create child branches under the project (also stale)
        # These simulate branches that weren't synced because the project was deleted
        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (b:GitLabBranch {id: $branch_id})
            SET b.lastupdated = $old_tag, b.name = 'main'
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_url=TEST_PROJECT_URL,
            branch_id=f"{TEST_PROJECT_URL}/tree/main",
            old_tag=TEST_UPDATE_TAG,
        )

        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (b:GitLabBranch {id: $branch_id})
            SET b.lastupdated = $old_tag, b.name = 'develop'
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_url=TEST_PROJECT_URL,
            branch_id=f"{TEST_PROJECT_URL}/tree/develop",
            old_tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GitLabBranch", ["id"])) == 2

        # Run cleanup with cascade_delete=True
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "org_url": TEST_ORG_URL,
        }
        GraphJob.from_node_schema(
            GitLabProjectSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: project and its children are deleted
        assert (
            len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 0
        ), "Stale project should be deleted"
        assert (
            len(check_nodes(neo4j_session, "GitLabBranch", ["id"])) == 0
        ), "Child branches should be cascade deleted"

    def test_project_cascade_preserves_fresh_branches(self, neo4j_session):
        """
        When cascade_delete runs, branches with current update_tag should be preserved.
        This handles the case where a branch was re-parented in the current sync.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create organization
        neo4j_session.run(
            """
            MERGE (o:GitLabOrganization {id: $org_url})
            SET o.lastupdated = $tag
            """,
            org_url=TEST_ORG_URL,
            tag=TEST_UPDATE_TAG_V2,
        )

        # Create stale project
        neo4j_session.run(
            """
            MERGE (p:GitLabProject {id: $project_url})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GitLabOrganization {id: $org_url})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_url=TEST_PROJECT_URL,
            org_url=TEST_ORG_URL,
            old_tag=TEST_UPDATE_TAG,  # Stale
        )

        # Create a stale branch (should be deleted)
        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (b:GitLabBranch {id: $branch_id})
            SET b.lastupdated = $old_tag, b.name = 'stale-branch'
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_url=TEST_PROJECT_URL,
            branch_id="stale-branch-id",
            old_tag=TEST_UPDATE_TAG,  # Stale
        )

        # Create a fresh branch (should be preserved - maybe re-parented)
        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (b:GitLabBranch {id: $branch_id})
            SET b.lastupdated = $current_tag, b.name = 'fresh-branch'
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_url=TEST_PROJECT_URL,
            branch_id="fresh-branch-id",
            current_tag=TEST_UPDATE_TAG_V2,  # Current - should be preserved
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GitLabBranch", ["id"])) == 2

        # Run cleanup with cascade_delete
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "org_url": TEST_ORG_URL,
        }
        GraphJob.from_node_schema(
            GitLabProjectSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: stale branch deleted, fresh branch preserved
        remaining_branches = check_nodes(neo4j_session, "GitLabBranch", ["id"])
        branch_ids = {b[0] for b in remaining_branches}

        assert "stale-branch-id" not in branch_ids, "Stale branch should be deleted"
        assert "fresh-branch-id" in branch_ids, "Fresh branch should be preserved"

    def test_project_cascade_deletes_dependency_files(self, neo4j_session):
        """
        When a stale GitLabProject is deleted with cascade_delete=True,
        its child dependency files should also be deleted.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create organization
        neo4j_session.run(
            """
            MERGE (o:GitLabOrganization {id: $org_url})
            SET o.lastupdated = $tag
            """,
            org_url=TEST_ORG_URL,
            tag=TEST_UPDATE_TAG_V2,
        )

        # Create stale project
        neo4j_session.run(
            """
            MERGE (p:GitLabProject {id: $project_url})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GitLabOrganization {id: $org_url})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_url=TEST_PROJECT_URL,
            org_url=TEST_ORG_URL,
            old_tag=TEST_UPDATE_TAG,
        )

        # Create child dependency file
        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (df:GitLabDependencyFile {id: $dep_file_id})
            SET df.lastupdated = $old_tag, df.path = 'requirements.txt'
            MERGE (p)-[:RESOURCE]->(df)
            """,
            project_url=TEST_PROJECT_URL,
            dep_file_id=f"{TEST_PROJECT_URL}/requirements.txt",
            old_tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GitLabDependencyFile", ["id"])) == 1

        # Run cleanup with cascade_delete=True
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "org_url": TEST_ORG_URL,
        }
        GraphJob.from_node_schema(
            GitLabProjectSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: project and dependency file are deleted
        assert len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 0
        assert (
            len(check_nodes(neo4j_session, "GitLabDependencyFile", ["id"])) == 0
        ), "Child dependency file should be cascade deleted"

    def test_without_cascade_delete_preserves_children(self, neo4j_session):
        """
        Without cascade_delete, child resources should remain as orphans.
        This is the default behavior for backward compatibility.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create organization
        neo4j_session.run(
            """
            MERGE (o:GitLabOrganization {id: $org_url})
            SET o.lastupdated = $tag
            """,
            org_url=TEST_ORG_URL,
            tag=TEST_UPDATE_TAG_V2,
        )

        # Create stale project
        neo4j_session.run(
            """
            MERGE (p:GitLabProject {id: $project_url})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GitLabOrganization {id: $org_url})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_url=TEST_PROJECT_URL,
            org_url=TEST_ORG_URL,
            old_tag=TEST_UPDATE_TAG,
        )

        # Create child branch
        neo4j_session.run(
            """
            MATCH (p:GitLabProject {id: $project_url})
            MERGE (b:GitLabBranch {id: $branch_id})
            SET b.lastupdated = $old_tag, b.name = 'main'
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_url=TEST_PROJECT_URL,
            branch_id=f"{TEST_PROJECT_URL}/tree/main",
            old_tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GitLabBranch", ["id"])) == 1

        # Run cleanup WITHOUT cascade_delete (default behavior)
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "org_url": TEST_ORG_URL,
        }
        GraphJob.from_node_schema(
            GitLabProjectSchema(),
            common_job_params,
            # cascade_delete defaults to False
        ).run(neo4j_session)

        # Verify: project is deleted but branch remains as orphan
        assert (
            len(check_nodes(neo4j_session, "GitLabProject", ["id"])) == 0
        ), "Stale project should be deleted"
        assert (
            len(check_nodes(neo4j_session, "GitLabBranch", ["id"])) == 1
        ), "Without cascade_delete, branch should remain as orphan"
