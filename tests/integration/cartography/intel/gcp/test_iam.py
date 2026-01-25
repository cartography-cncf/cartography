from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.iam
import tests.data.gcp.iam
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "PROJECT_ID": TEST_PROJECT_ID,
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


def _create_test_project(neo4j_session, project_id: str, update_tag: int):
    """Helper to create a GCPProject node for testing."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_roles(_mock_get_roles, _mock_get_sa, neo4j_session):
    """Test sync() loads GCP IAM roles correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify role nodes
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == {
        ("projects/project-abc/roles/customRole1",),
        ("roles/editor",),
        ("projects/project-abc/roles/customRole2",),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_service_accounts(_mock_get_roles, _mock_get_sa, neo4j_session):
    """Test sync() loads GCP IAM service accounts correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify service account nodes
    assert check_nodes(neo4j_session, "GCPServiceAccount", ["id"]) == {
        ("112233445566778899",),
        ("998877665544332211",),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_role_relationships(_mock_get_roles, _mock_get_sa, neo4j_session):
    """Test sync() creates correct relationships for GCP IAM roles."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project -> role RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPRole",
        "name",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole1"),
        (TEST_PROJECT_ID, "roles/editor"),
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole2"),
    }


@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE["accounts"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"],
)
def test_sync_gcp_iam_service_account_relationships(
    _mock_get_roles, _mock_get_sa, neo4j_session
):
    """Test sync() creates correct relationships for GCP IAM service accounts."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project -> service account RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPServiceAccount",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
