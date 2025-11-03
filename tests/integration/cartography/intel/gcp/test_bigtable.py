from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.bigtable as bigtable
from tests.data.gcp.bigtable import MOCK_APP_PROFILES
from tests.data.gcp.bigtable import MOCK_BACKUPS
from tests.data.gcp.bigtable import MOCK_CLUSTERS
from tests.data.gcp.bigtable import MOCK_INSTANCES
from tests.data.gcp.bigtable import MOCK_TABLES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"


def _create_prerequisite_nodes(neo4j_session):
    """
    Create the GCPProject node that this sync needs to link to.
    """
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.bigtable.get_bigtable_backups")
@patch("cartography.intel.gcp.bigtable.get_bigtable_app_profiles")
@patch("cartography.intel.gcp.bigtable.get_bigtable_tables")
@patch("cartography.intel.gcp.bigtable.get_bigtable_clusters")
@patch("cartography.intel.gcp.bigtable.get_bigtable_instances")
def test_sync_bigtable(
    mock_get_instances,
    mock_get_clusters,
    mock_get_tables,
    mock_get_app_profiles,
    mock_get_backups,
    neo4j_session,
):
    """
    Test the full sync() function for GCP Bigtable.
    """
    # Arrange: Mock all 5 API calls
    mock_get_instances.return_value = MOCK_INSTANCES["instances"]
    mock_get_clusters.return_value = MOCK_CLUSTERS["clusters"]
    mock_get_tables.return_value = MOCK_TABLES["tables"]
    mock_get_app_profiles.return_value = MOCK_APP_PROFILES["appProfiles"]
    mock_get_backups.return_value = MOCK_BACKUPS["backups"]

    # Arrange: Create prerequisite nodes
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # Act: Run the sync function
    bigtable.sync(
        neo4j_session,
        MagicMock(),  # Mock the bigtable_client
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Define expected IDs
    instance_id = "projects/test-project/instances/carto-bt-instance"
    cluster_id = (
        "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1"
    )
    table_id = (
        "projects/test-project/instances/carto-bt-instance/tables/carto-test-table"
    )
    app_profile_id = "projects/test-project/instances/carto-bt-instance/appProfiles/carto-app-profile"
    backup_id = "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1/backups/carto-table-backup"

    # Assert: Check all 5 new node types
    assert check_nodes(neo4j_session, "GCPBigtableInstance", ["id"]) == {(instance_id,)}
    assert check_nodes(neo4j_session, "GCPBigtableCluster", ["id"]) == {(cluster_id,)}
    assert check_nodes(neo4j_session, "GCPBigtableTable", ["id"]) == {(table_id,)}
    assert check_nodes(neo4j_session, "GCPBigtableAppProfile", ["id"]) == {
        (app_profile_id,)
    }
    assert check_nodes(neo4j_session, "GCPBigtableBackup", ["id"]) == {(backup_id,)}

    # Assert: Check all 11 relationships
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPBigtableInstance", "id", "RESOURCE"
    ) == {(TEST_PROJECT_ID, instance_id)}
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPBigtableCluster", "id", "RESOURCE"
    ) == {(TEST_PROJECT_ID, cluster_id)}
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPBigtableTable", "id", "RESOURCE"
    ) == {(TEST_PROJECT_ID, table_id)}
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPBigtableAppProfile", "id", "RESOURCE"
    ) == {(TEST_PROJECT_ID, app_profile_id)}
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPBigtableBackup", "id", "RESOURCE"
    ) == {(TEST_PROJECT_ID, backup_id)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableCluster",
        "id",
        "HAS_CLUSTER",
    ) == {(instance_id, cluster_id)}
    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableTable",
        "id",
        "HAS_TABLE",
    ) == {(instance_id, table_id)}
    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableAppProfile",
        "id",
        "HAS_APP_PROFILE",
    ) == {(instance_id, app_profile_id)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableAppProfile",
        "id",
        "GCPBigtableCluster",
        "id",
        "ROUTES_TO",
    ) == {(app_profile_id, cluster_id)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableCluster",
        "id",
        "GCPBigtableBackup",
        "id",
        "STORES_BACKUP",
    ) == {(cluster_id, backup_id)}
    assert check_rels(
        neo4j_session,
        "GCPBigtableTable",
        "id",
        "GCPBigtableBackup",
        "id",
        "BACKED_UP_AS",
    ) == {(table_id, backup_id)}
