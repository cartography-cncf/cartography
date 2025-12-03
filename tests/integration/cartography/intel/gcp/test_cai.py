from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cai
import tests.data.gcp.iam
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-123"
TEST_UPDATE_TAG = 123456789


def _create_test_project(neo4j_session):
    """Create a test GCP Project node"""
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.cai.get_gcp_service_accounts_cai")
@patch("cartography.intel.gcp.cai.get_gcp_roles_cai")
def test_sync_cai(mock_get_roles, mock_get_service_accounts, neo4j_session):
    """
    Test the full CAI sync function end-to-end with mocked API calls.
    Verifies that service accounts and roles are properly loaded into Neo4j.
    """
    # Arrange
    _create_test_project(neo4j_session)

    # Mock CAI API responses - extract data from CAI asset responses
    mock_get_service_accounts.return_value = [
        asset["resource"]["data"]
        for asset in tests.data.gcp.iam.CAI_SERVICE_ACCOUNTS_RESPONSE["assets"]
    ]
    mock_get_roles.return_value = [
        asset["resource"]["data"]
        for asset in tests.data.gcp.iam.CAI_ROLES_RESPONSE["assets"]
    ]

    # Create a mock CAI client
    mock_cai_client = MagicMock()

    # Act
    cartography.intel.gcp.cai.sync(
        neo4j_session,
        mock_cai_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert - verify mocks were called
    mock_get_service_accounts.assert_called_once_with(mock_cai_client, TEST_PROJECT_ID)
    mock_get_roles.assert_called_once_with(mock_cai_client, TEST_PROJECT_ID)

    # Assert - verify service account nodes were created
    expected_sa_nodes = {
        ("112233445566778899",),
        ("998877665544332211",),
    }
    assert check_nodes(neo4j_session, "GCPServiceAccount", ["id"]) == expected_sa_nodes

    # Assert - verify role nodes were created
    expected_role_nodes = {
        ("projects/project-123/roles/customRole1",),
        ("projects/project-123/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == expected_role_nodes

    # Assert - verify relationships to project
    expected_sa_rels = {
        (TEST_PROJECT_ID, "112233445566778899"),
        (TEST_PROJECT_ID, "998877665544332211"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPServiceAccount",
            "id",
            "RESOURCE",
        )
        == expected_sa_rels
    )

    expected_role_rels = {
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole1"),
        (TEST_PROJECT_ID, "projects/project-123/roles/customRole2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPRole",
            "name",
            "RESOURCE",
        )
        == expected_role_rels
    )
