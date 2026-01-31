"""
Integration tests for GCP cascade_delete cleanup behavior.

These tests verify that when parent nodes (Projects, Folders, Orgs) are deleted,
their child nodes are also deleted via cascade_delete to prevent orphaned nodes.

This addresses the scenario where a GCP project is deleted between syncs -
without cascade_delete, the project's resources (instances, buckets, etc.)
would remain as orphans since resource cleanup is scoped to PROJECT_ID.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp
import cartography.intel.gcp.crm.folders
import cartography.intel.gcp.crm.orgs
import cartography.intel.gcp.crm.projects
import cartography.intel.gcp.iam
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.folders import GCPFolderSchema
from cartography.models.gcp.crm.projects import GCPProjectSchema
from tests.integration import settings
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790
TEST_ORG_ID = "organizations/1337"
TEST_PROJECT_ID = "test-project-cascade"


class TestProjectCascadeDelete:
    """
    Test that cascade_delete on GCPProject cleanup removes orphaned child resources.
    """

    def test_project_cascade_deletes_child_resources(self, neo4j_session):
        """
        When a stale GCPProject is deleted with cascade_delete=True,
        its child resources should also be deleted.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create org
        neo4j_session.run(
            """
            MERGE (o:GCPOrganization {id: $org_id})
            SET o.lastupdated = $tag
            """,
            org_id=TEST_ORG_ID,
            tag=TEST_UPDATE_TAG_V2,  # Current tag - org is fresh
        )

        # Create stale project (old update tag)
        neo4j_session.run(
            """
            MERGE (p:GCPProject:Tenant {id: $project_id})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GCPOrganization {id: $org_id})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_id=TEST_PROJECT_ID,
            org_id=TEST_ORG_ID,
            old_tag=TEST_UPDATE_TAG,  # Old tag - project is stale
        )

        # Create child resources under the project (also stale)
        # These simulate resources that weren't synced because the project was deleted
        neo4j_session.run(
            """
            MATCH (p:GCPProject {id: $project_id})
            MERGE (i:GCPInstance {id: $instance_id})
            SET i.lastupdated = $old_tag
            MERGE (p)-[:RESOURCE]->(i)
            """,
            project_id=TEST_PROJECT_ID,
            instance_id=f"projects/{TEST_PROJECT_ID}/zones/us-central1-a/instances/orphan-instance",
            old_tag=TEST_UPDATE_TAG,
        )

        neo4j_session.run(
            """
            MATCH (p:GCPProject {id: $project_id})
            MERGE (b:GCPBucket {id: $bucket_id})
            SET b.lastupdated = $old_tag
            MERGE (p)-[:RESOURCE]->(b)
            """,
            project_id=TEST_PROJECT_ID,
            bucket_id=f"projects/{TEST_PROJECT_ID}/buckets/orphan-bucket",
            old_tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GCPInstance", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GCPBucket", ["id"])) == 1

        # Run cleanup with cascade_delete=True
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "ORG_RESOURCE_NAME": TEST_ORG_ID,
        }
        GraphJob.from_node_schema(
            GCPProjectSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: project and its children are deleted
        assert (
            len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 0
        ), "Stale project should be deleted"
        assert (
            len(check_nodes(neo4j_session, "GCPInstance", ["id"])) == 0
        ), "Child instance should be cascade deleted"
        assert (
            len(check_nodes(neo4j_session, "GCPBucket", ["id"])) == 0
        ), "Child bucket should be cascade deleted"

    def test_project_cascade_preserves_fresh_children(self, neo4j_session):
        """
        When cascade_delete runs, children with current update_tag should be preserved.
        This handles the case where a resource was re-parented in the current sync.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create org
        neo4j_session.run(
            """
            MERGE (o:GCPOrganization {id: $org_id})
            SET o.lastupdated = $tag
            """,
            org_id=TEST_ORG_ID,
            tag=TEST_UPDATE_TAG_V2,
        )

        # Create stale project
        neo4j_session.run(
            """
            MERGE (p:GCPProject:Tenant {id: $project_id})
            SET p.lastupdated = $old_tag
            WITH p
            MATCH (o:GCPOrganization {id: $org_id})
            MERGE (o)-[:RESOURCE]->(p)
            """,
            project_id=TEST_PROJECT_ID,
            org_id=TEST_ORG_ID,
            old_tag=TEST_UPDATE_TAG,  # Stale
        )

        # Create a stale child (should be deleted)
        neo4j_session.run(
            """
            MATCH (p:GCPProject {id: $project_id})
            MERGE (i:GCPInstance {id: $instance_id})
            SET i.lastupdated = $old_tag
            MERGE (p)-[:RESOURCE]->(i)
            """,
            project_id=TEST_PROJECT_ID,
            instance_id="stale-instance",
            old_tag=TEST_UPDATE_TAG,  # Stale
        )

        # Create a fresh child (should be preserved - maybe re-parented)
        neo4j_session.run(
            """
            MATCH (p:GCPProject {id: $project_id})
            MERGE (i:GCPInstance {id: $instance_id})
            SET i.lastupdated = $current_tag
            MERGE (p)-[:RESOURCE]->(i)
            """,
            project_id=TEST_PROJECT_ID,
            instance_id="fresh-instance",
            current_tag=TEST_UPDATE_TAG_V2,  # Current - should be preserved
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GCPInstance", ["id"])) == 2

        # Run cleanup with cascade_delete
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "ORG_RESOURCE_NAME": TEST_ORG_ID,
        }
        GraphJob.from_node_schema(
            GCPProjectSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: stale instance deleted, fresh instance preserved
        remaining_instances = check_nodes(neo4j_session, "GCPInstance", ["id"])
        instance_ids = {i[0] for i in remaining_instances}

        assert "stale-instance" not in instance_ids, "Stale instance should be deleted"
        assert "fresh-instance" in instance_ids, "Fresh instance should be preserved"


class TestFolderCascadeDelete:
    """
    Test cascade_delete on GCPFolder cleanup.
    """

    def test_folder_cascade_deletes_child_projects(self, neo4j_session):
        """
        When a stale GCPFolder is deleted with cascade_delete=True,
        child projects with RESOURCE relationship should also be deleted.

        Note: In GCP, projects have RESOURCE relationship to Organization,
        not to Folder. But folders can have nested folders as children.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")

        # Create org
        neo4j_session.run(
            """
            MERGE (o:GCPOrganization {id: $org_id})
            SET o.lastupdated = $tag
            """,
            org_id=TEST_ORG_ID,
            tag=TEST_UPDATE_TAG_V2,
        )

        # Create stale parent folder
        parent_folder_id = "folders/parent"
        neo4j_session.run(
            """
            MERGE (f:GCPFolder {id: $folder_id})
            SET f.lastupdated = $old_tag
            WITH f
            MATCH (o:GCPOrganization {id: $org_id})
            MERGE (o)-[:RESOURCE]->(f)
            """,
            folder_id=parent_folder_id,
            org_id=TEST_ORG_ID,
            old_tag=TEST_UPDATE_TAG,
        )

        # Create stale nested folder (child of parent folder)
        child_folder_id = "folders/child"
        neo4j_session.run(
            """
            MATCH (pf:GCPFolder {id: $parent_id})
            MERGE (cf:GCPFolder {id: $child_id})
            SET cf.lastupdated = $old_tag
            MERGE (pf)-[:RESOURCE]->(cf)
            """,
            parent_id=parent_folder_id,
            child_id=child_folder_id,
            old_tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GCPFolder", ["id"])) == 2

        # Run cleanup with cascade_delete
        common_job_params = {
            "UPDATE_TAG": TEST_UPDATE_TAG_V2,
            "ORG_RESOURCE_NAME": TEST_ORG_ID,
        }
        GraphJob.from_node_schema(
            GCPFolderSchema(), common_job_params, cascade_delete=True
        ).run(neo4j_session)

        # Verify: both folders deleted (parent was stale, child cascaded)
        remaining_folders = check_nodes(neo4j_session, "GCPFolder", ["id"])
        assert (
            len(remaining_folders) == 0
        ), f"All stale folders should be deleted, but found: {remaining_folders}"


class TestCascadeDeleteIntegration:
    """
    Integration test using the full GCP sync flow with cascade_delete.
    """

    def _make_fake_credentials(self):
        """Create a mock GCP credentials object for testing."""
        creds = MagicMock()
        creds.quota_project_id = "test-quota-project"
        creds.universe_domain = "googleapis.com"
        return creds

    @patch.object(
        cartography.intel.gcp,
        "get_gcp_credentials",
    )
    @patch.object(
        cartography.intel.gcp,
        "_sync_project_resources",
        return_value=None,
    )
    @patch.object(
        cartography.intel.gcp.crm.projects,
        "get_gcp_projects",
    )
    @patch.object(
        cartography.intel.gcp.crm.folders,
        "get_gcp_folders",
    )
    @patch.object(
        cartography.intel.gcp.crm.orgs,
        "get_gcp_organizations",
    )
    @patch.object(
        cartography.intel.gcp.iam,
        "get_gcp_predefined_roles",
        return_value=[],
    )
    @patch.object(
        cartography.intel.gcp.iam,
        "get_gcp_org_roles",
        return_value=[],
    )
    def test_full_sync_with_cascade_delete(
        self,
        mock_get_org_roles,
        mock_get_predefined_roles,
        mock_get_orgs,
        mock_get_folders,
        mock_get_projects,
        mock_sync_resources,
        mock_get_creds,
        neo4j_session,
    ):
        """
        Test the full GCP sync flow properly cascades deletions.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        mock_get_creds.return_value = self._make_fake_credentials()

        # First sync: org with project
        mock_get_orgs.return_value = [
            {
                "name": TEST_ORG_ID,
                "displayName": "test-org",
                "lifecycleState": "ACTIVE",
            }
        ]
        mock_get_folders.return_value = []
        mock_get_projects.return_value = [
            {
                "projectId": TEST_PROJECT_ID,
                "projectNumber": "123456",
                "name": "Test Project",
                "lifecycleState": "ACTIVE",
                "parent": TEST_ORG_ID,
            }
        ]

        config = Config(
            neo4j_uri=settings.get("NEO4J_URL"),
            update_tag=TEST_UPDATE_TAG,
        )
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

        # Create a child resource under the project
        neo4j_session.run(
            """
            MATCH (p:GCPProject {id: $project_id})
            MERGE (i:GCPInstance {id: $instance_id})
            SET i.lastupdated = $tag
            MERGE (p)-[:RESOURCE]->(i)
            """,
            project_id=TEST_PROJECT_ID,
            instance_id="orphan-instance",
            tag=TEST_UPDATE_TAG,
        )

        # Verify initial state
        assert len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 1
        assert len(check_nodes(neo4j_session, "GCPInstance", ["id"])) == 1

        # Second sync: project is deleted
        mock_get_projects.return_value = []  # Project no longer exists

        config.update_tag = TEST_UPDATE_TAG_V2
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

        # Verify: project and its child instance are both deleted
        assert (
            len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 0
        ), "Deleted project should be cleaned up"
        assert (
            len(check_nodes(neo4j_session, "GCPInstance", ["id"])) == 0
        ), "Child instance should be cascade deleted when project is deleted"
