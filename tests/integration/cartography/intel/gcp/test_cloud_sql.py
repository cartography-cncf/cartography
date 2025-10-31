from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cloud_sql as cloud_sql
from tests.data.gcp.cloud_sql import MOCK_DATABASES
from tests.data.gcp.cloud_sql import MOCK_INSTANCES
from tests.data.gcp.cloud_sql import MOCK_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"
TEST_INSTANCE_NAME = "carto-sql-test-instance"
TEST_INSTANCE_ID = f"projects/{TEST_PROJECT_ID}/instances/{TEST_INSTANCE_NAME}"
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


@patch("cartography.intel.gcp.cloud_sql.get_sql_users")
@patch("cartography.intel.gcp.cloud_sql.get_sql_databases")
@patch("cartography.intel.gcp.cloud_sql.get_sql_instances")
def test_sync_sql(
    mock_get_instances,
    mock_get_databases,
    mock_get_users,
    neo4j_session,
):
    """
    Test the full sync() function for GCP Cloud SQL.
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

    # Act: Run the sync function
    cloud_sql.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Check all 3 new node types
    assert check_nodes(neo4j_session, "GCPSqlInstance", ["id"]) == {
        (TEST_INSTANCE_ID,),
    }
    assert check_nodes(neo4j_session, "GCPSqlDatabase", ["id"]) == {
        (f"{TEST_INSTANCE_ID}/databases/carto-db-1",),
    }
    assert check_nodes(neo4j_session, "GCPSqlUser", ["id"]) == {
        (f"{TEST_INSTANCE_ID}/users/carto-user-1@%",),
        (f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%",),
    }

    # Assert: Check all 7 relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPSqlInstance",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, TEST_INSTANCE_ID)}

    assert check_rels(
        neo4j_session,
        "GCPSqlInstance",
        "id",
        "GCPVpc",
        "id",
        "ASSOCIATED_WITH",
    ) == {(TEST_INSTANCE_ID, TEST_VPC_ID)}

    assert check_rels(
        neo4j_session,
        "GCPSqlInstance",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {(TEST_INSTANCE_ID, TEST_SA_EMAIL)}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPSqlDatabase",
        "id",
        "RESOURCE",
    ) == {(TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/databases/carto-db-1")}

    assert check_rels(
        neo4j_session,
        "GCPSqlInstance",
        "id",
        "GCPSqlDatabase",
        "id",
        "CONTAINS",
    ) == {(TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/databases/carto-db-1")}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPSqlUser",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/users/carto-user-1@%"),
        (TEST_PROJECT_ID, f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%"),
    }

    assert check_rels(
        neo4j_session,
        "GCPSqlInstance",
        "id",
        "GCPSqlUser",
        "id",
        "HAS_USER",
    ) == {
        (TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/users/carto-user-1@%"),
        (TEST_INSTANCE_ID, f"{TEST_INSTANCE_ID}/users/postgres@cloudsqlproxy~%"),
    }
