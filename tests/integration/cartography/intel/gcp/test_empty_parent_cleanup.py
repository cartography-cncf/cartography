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

import cartography.intel.gcp as gcp
import cartography.intel.gcp.bigtable_backup as bigtable_backup
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"


def _create_gcp_project(neo4j_session, project_id: str, update_tag: int):
    """Create a GCPProject node for testing."""
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=project_id,
        tag=update_tag,
    )


def _create_stale_project_resource(
    neo4j_session,
    label: str,
    resource_id: str,
    project_id: str = TEST_PROJECT_ID,
):
    neo4j_session.run(
        f"""
        MERGE (r:{label} {{id: $resource_id}})
        SET r.lastupdated = $old_tag
        WITH r
        MATCH (p:GCPProject {{id: $project_id}})
        MERGE (p)-[:RESOURCE]->(r)
        """,
        resource_id=resource_id,
        project_id=project_id,
        old_tag=TEST_UPDATE_TAG - 1000,
    )


def test_project_resource_sync_cleans_bigtable_children_with_empty_instances(
    neo4j_session,
):
    """
    Verify real Bigtable child syncs clean stale data when instances sync returns [].

    This covers the project-level orchestration path where truthy checks on
    instances_raw would skip child cleanup when all instances were deleted.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_stale_project_resource(
        neo4j_session,
        "GCPBigtableCluster",
        "projects/test-project/instances/inst/clusters/old-cluster",
    )
    _create_stale_project_resource(
        neo4j_session,
        "GCPBigtableBackup",
        "projects/test-project/instances/inst/clusters/old-cluster/backups/old-backup",
    )

    credentials = MagicMock()
    bigtable_client = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    with (
        patch(
            "cartography.intel.gcp._services_enabled_on_project",
            return_value={gcp.service_names.bigtable},
        ),
        patch("cartography.intel.gcp.build_client", return_value=bigtable_client),
        patch(
            "cartography.intel.gcp.bigtable_instance.get_bigtable_instances",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.bigtable_cluster.get_bigtable_clusters",
            side_effect=AssertionError("clusters should not be fetched"),
        ),
        patch(
            "cartography.intel.gcp.bigtable_table.get_bigtable_tables",
            side_effect=AssertionError("tables should not be fetched"),
        ),
        patch(
            "cartography.intel.gcp.bigtable_app_profile.get_bigtable_app_profiles",
            side_effect=AssertionError("app profiles should not be fetched"),
        ),
        patch(
            "cartography.intel.gcp.bigtable_backup.get_bigtable_backups",
            side_effect=AssertionError("backups should not be fetched"),
        ),
    ):
        gcp._sync_project_resources(
            neo4j_session,
            [{"projectId": TEST_PROJECT_ID}],
            TEST_UPDATE_TAG,
            common_job_parameters,
            credentials,
            requested_syncs={"bigtable"},
        )

    assert check_nodes(neo4j_session, "GCPBigtableCluster", ["id"]) == set()
    assert check_nodes(neo4j_session, "GCPBigtableBackup", ["id"]) == set()


def test_project_resource_sync_cleans_bigtable_backups_with_empty_clusters(
    neo4j_session,
):
    """
    Verify real backup sync cleans stale data when cluster sync returns [].

    This covers the project-level orchestration path where truthy checks on
    clusters_raw would skip backup cleanup when all clusters were deleted.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_stale_project_resource(
        neo4j_session,
        "GCPBigtableBackup",
        "projects/test-project/instances/inst/clusters/c1/backups/old-backup",
    )

    credentials = MagicMock()
    bigtable_client = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    instances_raw = [{"name": "projects/test-project/instances/inst"}]

    with (
        patch(
            "cartography.intel.gcp._services_enabled_on_project",
            return_value={gcp.service_names.bigtable},
        ),
        patch("cartography.intel.gcp.build_client", return_value=bigtable_client),
        patch(
            "cartography.intel.gcp.bigtable_instance.get_bigtable_instances",
            return_value=instances_raw,
        ),
        patch(
            "cartography.intel.gcp.bigtable_cluster.get_bigtable_clusters",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.bigtable_table.get_bigtable_tables", return_value=[]
        ),
        patch(
            "cartography.intel.gcp.bigtable_app_profile.get_bigtable_app_profiles",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.bigtable_backup.get_bigtable_backups",
            side_effect=AssertionError("backups should not be fetched"),
        ),
    ):
        gcp._sync_project_resources(
            neo4j_session,
            [{"projectId": TEST_PROJECT_ID}],
            TEST_UPDATE_TAG,
            common_job_parameters,
            credentials,
            requested_syncs={"bigtable"},
        )

    assert check_nodes(neo4j_session, "GCPBigtableBackup", ["id"]) == set()


def test_project_resource_sync_cleans_deployed_models_with_empty_endpoints(
    neo4j_session,
):
    """
    Verify real deployed model sync cleans stale data when endpoint sync returns [].

    This covers the project-level orchestration path where truthy checks on
    endpoints_raw would skip deployed model cleanup when all endpoints were deleted.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_gcp_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    _create_stale_project_resource(
        neo4j_session,
        "GCPVertexAIDeployedModel",
        "projects/test-project/locations/us-central1/endpoints/123/deployedModels/456",
    )

    credentials = MagicMock()
    aiplatform_client = MagicMock()
    aiplatform_client._http.credentials = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    with (
        patch(
            "cartography.intel.gcp._services_enabled_on_project",
            return_value={gcp.service_names.aiplatform},
        ),
        patch("cartography.intel.gcp.build_client", return_value=aiplatform_client),
        patch("cartography.intel.gcp.get_vertex_ai_locations", return_value=["us"]),
        patch(
            "cartography.intel.gcp.vertex.models.get_vertex_ai_models_for_location",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.vertex.endpoints.get_vertex_ai_endpoints_for_location",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.vertex.instances.get_workbench_api_locations",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.vertex.training_pipelines.get_vertex_ai_training_pipelines_for_location",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.vertex.feature_groups.get_feature_groups_for_location",
            return_value=[],
        ),
        patch(
            "cartography.intel.gcp.vertex.datasets.get_vertex_ai_datasets_for_location",
            return_value=[],
        ),
    ):
        gcp._sync_project_resources(
            neo4j_session,
            [{"projectId": TEST_PROJECT_ID}],
            TEST_UPDATE_TAG,
            common_job_parameters,
            credentials,
            requested_syncs={"aiplatform"},
        )

    assert check_nodes(neo4j_session, "GCPVertexAIDeployedModel", ["id"]) == set()


@patch("cartography.intel.gcp.bigtable_backup.get_bigtable_backups")
def test_cleanup_preserves_current_removes_stale(mock_get_backups, neo4j_session):
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
