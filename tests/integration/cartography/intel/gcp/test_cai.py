from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp
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


@patch("cartography.intel.gcp.cai.sync")
@patch("cartography.intel.gcp.iam.sync")
@patch("cartography.intel.gcp._services_enabled_on_project")
@patch("cartography.intel.gcp.build_client")
@patch("cartography.intel.gcp.google_auth_default")
def test_sync_project_resources_falls_back_to_cai_when_iam_disabled(
    mock_google_auth_default,
    mock_build_client,
    mock_services,
    mock_iam_sync,
    mock_cai_sync,
    neo4j_session,
):
    """Ensure we call CAI sync when IAM API is disabled but CAI is enabled."""

    projects = [{"projectId": TEST_PROJECT_ID}]
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    created_clients = {}

    mock_services.return_value = (
        set()
    )  # IAM disabled, CAI not enabled on target project

    # Simulate ADC credentials with a quota project available
    mock_creds = MagicMock()
    mock_creds.quota_project_id = "adc-quota-project"
    mock_google_auth_default.return_value = (mock_creds, "adc-quota-project")

    def _build_client(service, version, credentials=None, quota_project_id=None):
        client = MagicMock(name=f"{service}_client")
        created_clients[(service, version)] = client
        return client

    mock_build_client.side_effect = _build_client

    cartography.intel.gcp._sync_project_resources(
        neo4j_session,
        projects,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    mock_services.assert_called_once()
    assert ("serviceusage", "v1") in created_clients
    mock_iam_sync.assert_not_called()

    mock_cai_sync.assert_called_once()
    called_session, cai_client, project_id, update_tag, _ = mock_cai_sync.call_args[0]
    assert called_session is neo4j_session
    assert cai_client is created_clients[("cloudasset", "v1")]
    assert project_id == TEST_PROJECT_ID
    assert update_tag == TEST_UPDATE_TAG
