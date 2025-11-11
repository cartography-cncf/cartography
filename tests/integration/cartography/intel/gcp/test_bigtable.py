from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.bigtable_app_profile as bigtable_app_profile
import cartography.intel.gcp.bigtable_backup as bigtable_backup
import cartography.intel.gcp.bigtable_cluster as bigtable_cluster
import cartography.intel.gcp.bigtable_instance as bigtable_instance
import cartography.intel.gcp.bigtable_table as bigtable_table
from tests.data.gcp.bigtable import MOCK_APP_PROFILES
from tests.data.gcp.bigtable import MOCK_BACKUPS
from tests.data.gcp.bigtable import MOCK_CLUSTERS
from tests.data.gcp.bigtable import MOCK_INSTANCES
from tests.data.gcp.bigtable import MOCK_TABLES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_INSTANCE_ID = "projects/test-project/instances/carto-bt-instance"
TEST_CLUSTER_ID = (
    "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1"
)
TEST_TABLE_ID = (
    "projects/test-project/instances/carto-bt-instance/tables/carto-test-table"
)
TEST_APP_PROFILE_ID = (
    "projects/test-project/instances/carto-bt-instance/appProfiles/carto-app-profile"
)
TEST_BACKUP_ID = "projects/test-project/instances/carto-bt-instance/clusters/carto-bt-cluster-c1/backups/carto-table-backup"


def _create_prerequisite_nodes(neo4j_session):
    """
    Create the GCPProject node that this sync needs to link to.
    """
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.bigtable_backup.get_bigtable_backups")
@patch("cartography.intel.gcp.bigtable_app_profile.get_bigtable_app_profiles")
@patch("cartography.intel.gcp.bigtable_table.get_bigtable_tables")
@patch("cartography.intel.gcp.bigtable_cluster.get_bigtable_clusters")
@patch("cartography.intel.gcp.bigtable_instance.get_bigtable_instances")
def test_sync_bigtable_modules(
    mock_get_instances,
    mock_get_clusters,
    mock_get_tables,
    mock_get_app_profiles,
    mock_get_backups,
    neo4j_session,
):
    """
    Test the sync functions for the refactored Bigtable modules.
    This test simulates the behavior of the main gcp/__init__.py file.
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
    mock_bigtable_client = MagicMock()

    # Act: Run the sync functions in the same order as gcp/__init__.py
    instances_raw = bigtable_instance.sync_bigtable_instances(
        neo4j_session,
        mock_bigtable_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    clusters_raw = bigtable_cluster.sync_bigtable_clusters(
        neo4j_session,
        mock_bigtable_client,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigtable_table.sync_bigtable_tables(
        neo4j_session,
        mock_bigtable_client,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigtable_app_profile.sync_bigtable_app_profiles(
        neo4j_session,
        mock_bigtable_client,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigtable_backup.sync_bigtable_backups(
        neo4j_session,
        mock_bigtable_client,
        clusters_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Check all 5 new node types
    assert check_nodes(neo4j_session, "GCPBigtableInstance", ["id"]) == {
        (TEST_INSTANCE_ID,)
    }
    assert check_nodes(neo4j_session, "GCPBigtableCluster", ["id"]) == {
        (TEST_CLUSTER_ID,)
    }
    assert check_nodes(neo4j_session, "GCPBigtableTable", ["id"]) == {(TEST_TABLE_ID,)}
    assert check_nodes(neo4j_session, "GCPBigtableAppProfile", ["id"]) == {
        (TEST_APP_PROFILE_ID,)
    }
    assert check_nodes(neo4j_session, "GCPBigtableBackup", ["id"]) == {
        (TEST_BACKUP_ID,)
    }

    # Assert: Check all 11 relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigtableInstance",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_INSTANCE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigtableCluster",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_CLUSTER_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigtableTable",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_TABLE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigtableAppProfile",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_APP_PROFILE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigtableBackup",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_BACKUP_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableCluster",
        "id",
        "HAS_CLUSTER",
    ) == {(TEST_INSTANCE_ID, TEST_CLUSTER_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableTable",
        "id",
        "HAS_TABLE",
    ) == {(TEST_INSTANCE_ID, TEST_TABLE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableInstance",
        "id",
        "GCPBigtableAppProfile",
        "id",
        "HAS_APP_PROFILE",
    ) == {(TEST_INSTANCE_ID, TEST_APP_PROFILE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableAppProfile",
        "id",
        "GCPBigtableCluster",
        "id",
        "ROUTES_TO",
    ) == {(TEST_APP_PROFILE_ID, TEST_CLUSTER_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableCluster",
        "id",
        "GCPBigtableBackup",
        "id",
        "STORES_BACKUP",
    ) == {(TEST_CLUSTER_ID, TEST_BACKUP_ID)}

    assert check_rels(
        neo4j_session,
        "GCPBigtableTable",
        "id",
        "GCPBigtableBackup",
        "id",
        "BACKED_UP_AS",
    ) == {(TEST_TABLE_ID, TEST_BACKUP_ID)}
