from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cai
import tests.data.gcp.iam
from tests.integration.cartography.intel.gcp.test_iam import _create_test_project
from tests.integration.cartography.intel.gcp.test_iam import TEST_PROJECT_ID
from tests.integration.cartography.intel.gcp.test_iam import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


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


@patch("cartography.intel.gcp.cai.get_gcp_service_accounts_cai")
@patch("cartography.intel.gcp.cai.get_gcp_roles_cai")
def test_sync_cai_with_predefined_roles(
    mock_get_roles, mock_get_service_accounts, neo4j_session
):
    """
    Test that predefined roles passed from the quota project are properly merged
    with custom roles from CAI.
    """
    # Arrange
    _create_test_project(neo4j_session)
    # Clear roles from previous test
    neo4j_session.run("MATCH (r:GCPRole) DETACH DELETE r")

    # Mock CAI API responses - only custom roles from CAI
    mock_get_service_accounts.return_value = []
    mock_get_roles.return_value = [
        asset["resource"]["data"]
        for asset in tests.data.gcp.iam.CAI_ROLES_RESPONSE["assets"]
    ]

    # Use the predefined role from LIST_ROLES_RESPONSE (roles/editor)
    # This simulates fetching predefined roles from the quota project's IAM API
    predefined_roles = [
        role
        for role in tests.data.gcp.iam.LIST_ROLES_RESPONSE["roles"]
        if role["name"].startswith("roles/")
    ]

    # Act
    cartography.intel.gcp.cai.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        predefined_roles=predefined_roles,
    )

    # Assert - verify both custom and predefined role nodes were created
    expected_role_nodes = {
        # Custom roles from CAI
        ("projects/project-123/roles/customRole1", "CUSTOM"),
        ("projects/project-123/roles/customRole2", "CUSTOM"),
        # Predefined role from quota project IAM API
        ("roles/editor", "BASIC"),
    }
    assert (
        check_nodes(neo4j_session, "GCPRole", ["id", "role_type"])
        == expected_role_nodes
    )
