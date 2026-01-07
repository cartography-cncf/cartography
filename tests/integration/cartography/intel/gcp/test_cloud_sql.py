from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloud_sql_backup_config as cloud_sql_backup_config
import cartography.intel.gcp.cloud_sql_database as cloud_sql_database
import cartography.intel.gcp.cloud_sql_instance as cloud_sql_instance
import cartography.intel.gcp.cloud_sql_user as cloud_sql_user
from tests.data.gcp.cloud_sql import MOCK_DATABASES
from tests.data.gcp.cloud_sql import MOCK_INSTANCES
from tests.data.gcp.cloud_sql import MOCK_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_INSTANCE_NAME = "carto-sql-test-instance"
TEST_INSTANCE_ID = f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{TEST_PROJECT_ID}/instances/{TEST_INSTANCE_NAME}"
TEST_VPC_ID = f"projects/{TEST_PROJECT_ID}/global/networks/carto-sql-vpc"
TEST_SA_EMAIL = "test-sa@test-project.iam.gserviceaccount.com"


def _create_prerequisite_nodes(neo4j_session):
    """
    Create nodes that the Cloud SQL sync expects to already exist.
    """
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (v:GCPVpc {id: $vpc_id}) SET v.lastupdated = $tag",
        vpc_id=TEST_VPC_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sa:GCPServiceAccount {email: $sa_email}) SET sa.lastupdated = $tag",
        sa_email=TEST_SA_EMAIL,
        tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.cloud_sql_user.get_sql_users")
@patch("cartography.intel.gcp.cloud_sql_database.get_sql_databases")
@patch("cartography.intel.gcp.cloud_sql_instance.get_sql_instances")
def test_sync_sql(
    mock_get_instances,
    mock_get_databases,
    mock_get_users,
    neo4j_session,
):
    """
    Test the full sync() functions for the refactored GCP Cloud SQL modules.
    This test simulates the behavior of the main gcp/__init__.py file.
    """
    # Arrange: Mock all 3 API calls
    mock_get_instances.return_value = MOCK_INSTANCES["items"]
    mock_get_databases.return_value = MOCK_DATABASES["items"]
    mock_get_users.return_value = MOCK_USERS["items"]

    # Arrange: Create prerequisite nodes
    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_sql_client = MagicMock()

    instances_raw = cloud_sql_instance.sync_sql_instances(
        neo4j_session,
        mock_sql_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_sql_database.sync_sql_databases(
        neo4j_session,
        mock_sql_client,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_sql_user.sync_sql_users(
        neo4j_session,
        mock_sql_client,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    cloud_sql_backup_config.sync_sql_backup_configs(
        neo4j_session,
        instances_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Check all 4 new node types
    assert check_nodes(neo4j_session, "GCPCloudSQLInstance", ["id"]) == {
        (TEST_INSTANCE_ID,),
    }
    assert check_nodes(neo4j_session, "GCPCloudSQLDatabase", ["id"]) == {
        (f"{TEST_INSTANCE_ID}/databases/carto-db-1",),
    }
    assert check_nodes(neo4j_session, "GCPCloudSQLUser", ["id"]) == {
        (f"{TEST_INSTANCE_ID}/users/carto-user-1@%",),
        (f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%",),
    }
    assert check_nodes(neo4j_session, "GCPCloudSQLBackupConfiguration", ["id"]) == {
        (f"{TEST_INSTANCE_ID}/backupConfig",),
    }

    # Assert: Check all 9 relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudSQLInstance",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_INSTANCE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPCloudSQLInstance",
        "id",
        "GCPVpc",
        "id",
        "ASSOCIATED_WITH",
    ) == {(TEST_INSTANCE_ID, TEST_VPC_ID)}

    assert check_rels(
        neo4j_session,
        "GCPCloudSQLInstance",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_INSTANCE_ID, TEST_SA_EMAIL)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudSQLDatabase",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/databases/carto-db-1")}

    assert check_rels(
        neo4j_session,
        "GCPCloudSQLInstance",
        "id",
        "GCPCloudSQLDatabase",
        "id",
        "CONTAINS",
    ) == {(TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/databases/carto-db-1")}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudSQLUser",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/users/carto-user-1@%"),
        (TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%"),
    }

    assert check_rels(
        neo4j_session,
        "GCPCloudSQLInstance",
        "id",
        "GCPCloudSQLUser",
        "id",
        "HAS_USER",
    ) == {
        (TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/users/carto-user-1@%"),
        (TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%"),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPCloudSQLBackupConfiguration",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/backupConfig")}

    assert check_rels(
        neo4j_session,
        "GCPCloudSQLInstance",
        "id",
        "GCPCloudSQLBackupConfiguration",
        "id",
        "HAS_BACKUP_CONFIG",
    ) == {(TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/backupConfig")}
