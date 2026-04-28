from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.cai
import tests.data.gcp.iam
from tests.integration.cartography.intel.gcp.test_iam import _create_test_project
from tests.integration.cartography.intel.gcp.test_iam import TEST_PROJECT_ID
from tests.integration.cartography.intel.gcp.test_iam import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

COMMON_JOB_PARAMS = {
    "PROJECT_ID": TEST_PROJECT_ID,
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


@patch("cartography.intel.gcp.cai.get_gcp_service_accounts_cai")
@patch("cartography.intel.gcp.cai.get_gcp_roles_cai")
def test_sync_cai(mock_get_roles, mock_get_service_accounts, neo4j_session):
    """
    Test the full CAI sync function end-to-end with mocked API calls.
    Verifies that service accounts and project-level roles are properly loaded into Neo4j.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

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
        COMMON_JOB_PARAMS,
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

    # Assert - verify role nodes were created (only project custom roles)
    expected_role_nodes = {
        ("projects/project-abc/roles/customRole1",),
        ("projects/project-abc/roles/customRole2",),
    }
    assert check_nodes(neo4j_session, "GCPRole", ["id"]) == expected_role_nodes

    # Assert - verify service account relationships to project
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

    # Assert - verify role relationships to project (sub_resource)
    # Project-level roles are sub-resources of their project, not the organization
    expected_role_project_rels = {
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole1"),
        (TEST_PROJECT_ID, "projects/project-abc/roles/customRole2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPRole",
            "name",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_role_project_rels
    )


@patch("cartography.intel.gcp.cai.get_gcp_service_accounts_cai")
@patch("cartography.intel.gcp.cai.get_gcp_roles_cai")
def test_sync_cai_filters_non_project_roles(
    mock_get_roles, mock_get_service_accounts, neo4j_session
):
    """
    Test that CAI sync filters out non-project roles.
    Predefined roles and org-level roles should be synced at the organization level via sync_org_iam().
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Mock CAI API responses - include a mix of role types
    mock_get_service_accounts.return_value = []
    # CAI API might return predefined roles in some edge cases; they should be filtered
    mock_get_roles.return_value = [
        asset["resource"]["data"]
        for asset in tests.data.gcp.iam.CAI_ROLES_RESPONSE["assets"]
    ] + [
        # Add a predefined role that should be filtered out
        {
            "name": "roles/viewer",
            "title": "Viewer",
            "description": "View access",
        }
    ]

    # Act
    cartography.intel.gcp.cai.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert - verify ONLY custom project roles were created, NOT predefined roles
    expected_role_nodes = {
        # Custom roles from CAI
        ("projects/project-abc/roles/customRole1", "CUSTOM", "PROJECT"),
        ("projects/project-abc/roles/customRole2", "CUSTOM", "PROJECT"),
        # Predefined roles should NOT be created here
    }
    assert (
        check_nodes(neo4j_session, "GCPRole", ["id", "role_type", "scope"])
        == expected_role_nodes
    )


@patch("cartography.intel.gcp.cai.get_gcp_service_accounts_cai")
@patch("cartography.intel.gcp.cai.get_gcp_roles_cai")
def test_sync_cai_role_scope_property(
    mock_get_roles, mock_get_service_accounts, neo4j_session
):
    """
    Test that CAI sync sets the scope property correctly on project custom roles.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    # Mock CAI API responses
    mock_get_service_accounts.return_value = []
    mock_get_roles.return_value = [
        asset["resource"]["data"]
        for asset in tests.data.gcp.iam.CAI_ROLES_RESPONSE["assets"]
    ]

    # Act
    cartography.intel.gcp.cai.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert - verify scope property is set correctly
    result = neo4j_session.run(
        """
        MATCH (r:GCPRole)
        RETURN r.name as name, r.scope as scope, r.role_type as role_type
        ORDER BY r.name
        """
    )
    roles = {
        record["name"]: (record["scope"], record["role_type"]) for record in result
    }

    # Custom project roles should have PROJECT scope and CUSTOM type
    assert roles["projects/project-abc/roles/customRole1"] == ("PROJECT", "CUSTOM")
    assert roles["projects/project-abc/roles/customRole2"] == ("PROJECT", "CUSTOM")
