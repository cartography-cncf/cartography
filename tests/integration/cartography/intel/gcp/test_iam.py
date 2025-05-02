import cartography.intel.gcp.iam
import tests.data.gcp.iam
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = 'project-123'
TEST_UPDATE_TAG = 123456789


def _create_test_project(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gcp_roles(neo4j_session):
    # Arrange
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_ROLES_RESPONSE['roles']

    # Act
    cartography.intel.gcp.iam.load_gcp_roles(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("projects/project-123/roles/customRole1",),
        ("roles/editor",),
        ("projects/project-123/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, 'GCPRole', ['id']) == expected_nodes

    # Check relationships
    expected_rels = {
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole1"),
        (TEST_PROJECT_ID, "roles/editor"),
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole2"),
    }
    assert check_rels(
        neo4j_session,
        'GCPProject',
        'id',
        'GCPRole',
        'name',
        'RESOURCE',
    ) == expected_rels


def test_load_gcp_service_accounts(neo4j_session):
    # Arrange
    _create_test_project(neo4j_session)
    data = tests.data.gcp.iam.LIST_SERVICE_ACCOUNTS_RESPONSE['accounts']

    # Act
    cartography.intel.gcp.iam.load_gcp_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("112233445566778899",),
        ("998877665544332211",),
    }
    assert check_nodes(neo4j_session, 'GCPServiceAccount', ['id']) == expected_nodes

    # Check relationships
    expected_rels = {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
    assert check_rels(
        neo4j_session,
        'GCPProject',
        'id',
        'GCPServiceAccount',
        'id',
        'RESOURCE',
    ) == expected_rels
