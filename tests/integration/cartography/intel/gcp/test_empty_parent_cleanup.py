"""
Integration tests for GCP cleanup behavior when parent resource lists are empty.

These tests verify that cleanup runs correctly even when parent resources
(instances, endpoints, etc.) return empty lists, preventing stale child
nodes from accumulating.

This addresses the bug where truthy checks on parent lists (if clusters_raw:)
would skip cleanup when the list was empty, leaving orphaned child nodes.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.bigtable_backup as bigtable_backup
import cartography.intel.gcp.bigtable_cluster as bigtable_cluster
from cartography.intel.gcp.vertex.deployed_models import sync_vertex_ai_deployed_models
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790
TEST_PROJECT_ID = "test-project"


def _create_gcp_project(neo4j_session, project_id: str, update_tag: int):
    """Create a GCPProject node for testing."""
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=project_id,
        tag=update_tag,
    )


class TestBigtableBackupCleanupWithEmptyClusters:
    """
    Test that Bigtable backup cleanup runs even when clusters list is empty.

    Scenario:
    1. First sync: Instance has clusters with backups
    2. Second sync: Instance deleted, clusters_raw is empty []
    3. Expected: Backup cleanup should still run and remove stale backups
    """

    def test_backup_cleanup_runs_with_empty_clusters(self, neo4j_session):
        """Verify backup cleanup runs when clusters list is empty."""
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Create a stale backup node (simulating previous sync)
        neo4j_session.run(
            """
            MERGE (b:GCPBigtableBackup {id: $backup_id})
            SET b.lastupdated = $old_tag
            WITH b
            MATCH (p:GCPProject {id: $project_id})
            MERGE (p)-[:RESOURCE]->(b)
            """,
            backup_id="projects/test-project/instances/inst/clusters/c1/backups/old-backup",
            project_id=TEST_PROJECT_ID,
            old_tag=TEST_UPDATE_TAG - 1000,  # Old update tag = stale
        )

        # Verify stale backup exists
        assert len(check_nodes(neo4j_session, "GCPBigtableBackup", ["id"])) == 1

        # Run backup sync with empty clusters list
        # This simulates the scenario where all instances were deleted
        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "PROJECT_ID": TEST_PROJECT_ID,
        }
        mock_client = MagicMock()

        # Empty clusters list - previously this would skip cleanup
        bigtable_backup.sync_bigtable_backups(
            neo4j_session,
            mock_client,
            [],  # Empty clusters list
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Verify stale backup was cleaned up
        remaining_backups = check_nodes(neo4j_session, "GCPBigtableBackup", ["id"])
        assert len(remaining_backups) == 0, (
            f"Stale backups should be cleaned up even with empty clusters list, "
            f"but found: {remaining_backups}"
        )


class TestBigtableClusterCleanupWithEmptyInstances:
    """
    Test that Bigtable cluster cleanup runs even when instances list is empty.
    """

    def test_cluster_cleanup_runs_with_empty_instances(self, neo4j_session):
        """Verify cluster cleanup runs when instances list is empty."""
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Create a stale cluster node
        neo4j_session.run(
            """
            MERGE (c:GCPBigtableCluster {id: $cluster_id})
            SET c.lastupdated = $old_tag
            WITH c
            MATCH (p:GCPProject {id: $project_id})
            MERGE (p)-[:RESOURCE]->(c)
            """,
            cluster_id="projects/test-project/instances/inst/clusters/old-cluster",
            project_id=TEST_PROJECT_ID,
            old_tag=TEST_UPDATE_TAG - 1000,
        )

        # Verify stale cluster exists
        assert len(check_nodes(neo4j_session, "GCPBigtableCluster", ["id"])) == 1

        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "PROJECT_ID": TEST_PROJECT_ID,
        }
        mock_client = MagicMock()

        # Run cluster sync with empty instances list
        bigtable_cluster.sync_bigtable_clusters(
            neo4j_session,
            mock_client,
            [],  # Empty instances list
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Verify stale cluster was cleaned up
        remaining_clusters = check_nodes(neo4j_session, "GCPBigtableCluster", ["id"])
        assert len(remaining_clusters) == 0, (
            f"Stale clusters should be cleaned up even with empty instances list, "
            f"but found: {remaining_clusters}"
        )


class TestVertexAIDeployedModelsCleanupWithEmptyEndpoints:
    """
    Test that Vertex AI deployed models cleanup runs even when endpoints list is empty.
    """

    def test_deployed_models_cleanup_runs_with_empty_endpoints(self, neo4j_session):
        """Verify deployed models cleanup runs when endpoints list is empty."""
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Create a stale deployed model node
        neo4j_session.run(
            """
            MERGE (dm:GCPVertexAIDeployedModel {id: $model_id})
            SET dm.lastupdated = $old_tag
            WITH dm
            MATCH (p:GCPProject {id: $project_id})
            MERGE (p)-[:RESOURCE]->(dm)
            """,
            model_id="projects/test-project/locations/us-central1/endpoints/123/deployedModels/456",
            project_id=TEST_PROJECT_ID,
            old_tag=TEST_UPDATE_TAG - 1000,
        )

        # Verify stale deployed model exists
        assert len(check_nodes(neo4j_session, "GCPVertexAIDeployedModel", ["id"])) == 1

        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "PROJECT_ID": TEST_PROJECT_ID,
        }

        # Run deployed models sync with empty endpoints list
        sync_vertex_ai_deployed_models(
            neo4j_session,
            [],  # Empty endpoints list
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Verify stale deployed model was cleaned up
        remaining_models = check_nodes(
            neo4j_session, "GCPVertexAIDeployedModel", ["id"]
        )
        assert len(remaining_models) == 0, (
            f"Stale deployed models should be cleaned up even with empty endpoints list, "
            f"but found: {remaining_models}"
        )


class TestCleanupPreservesCurrentData:
    """
    Test that cleanup correctly preserves data from the current sync
    while removing stale data.
    """

    @patch("cartography.intel.gcp.bigtable_backup.get_bigtable_backups")
    def test_cleanup_preserves_current_removes_stale(
        self, mock_get_backups, neo4j_session
    ):
        """
        Verify that cleanup removes stale nodes but preserves current ones.
        """
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Create a cluster for testing
        cluster_id = "projects/test-project/instances/inst/clusters/cluster1"
        neo4j_session.run(
            """
            MERGE (c:GCPBigtableCluster {id: $cluster_id})
            SET c.lastupdated = $tag, c.name = $cluster_id
            WITH c
            MATCH (p:GCPProject {id: $project_id})
            MERGE (p)-[:RESOURCE]->(c)
            """,
            cluster_id=cluster_id,
            project_id=TEST_PROJECT_ID,
            tag=TEST_UPDATE_TAG,
        )

        # Create stale backup (old update tag)
        neo4j_session.run(
            """
            MERGE (b:GCPBigtableBackup {id: $backup_id})
            SET b.lastupdated = $old_tag
            WITH b
            MATCH (p:GCPProject {id: $project_id})
            MERGE (p)-[:RESOURCE]->(b)
            """,
            backup_id="projects/test-project/instances/inst/clusters/cluster1/backups/stale-backup",
            project_id=TEST_PROJECT_ID,
            old_tag=TEST_UPDATE_TAG - 1000,
        )

        # Mock API to return a current backup
        mock_get_backups.return_value = [
            {
                "name": "projects/test-project/instances/inst/clusters/cluster1/backups/current-backup",
                "sourceTable": "projects/test-project/instances/inst/tables/table1",
            }
        ]

        common_job_parameters = {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "PROJECT_ID": TEST_PROJECT_ID,
        }
        mock_client = MagicMock()

        # Provide cluster data so backups can be fetched
        clusters = [{"name": cluster_id}]

        bigtable_backup.sync_bigtable_backups(
            neo4j_session,
            mock_client,
            clusters,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

        # Verify: current backup exists, stale backup is gone
        remaining_backups = check_nodes(neo4j_session, "GCPBigtableBackup", ["id"])
        backup_ids = {b[0] for b in remaining_backups}

        assert (
            "projects/test-project/instances/inst/clusters/cluster1/backups/current-backup"
            in backup_ids
        ), "Current backup should be preserved"
        assert (
            "projects/test-project/instances/inst/clusters/cluster1/backups/stale-backup"
            not in backup_ids
        ), "Stale backup should be cleaned up"
