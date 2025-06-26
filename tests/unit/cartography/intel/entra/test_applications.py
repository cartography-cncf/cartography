from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.entra.applications import cleanup_app_role_assignments
from cartography.intel.entra.applications import cleanup_applications
from cartography.intel.entra.applications import load_app_role_assignments
from cartography.intel.entra.applications import load_applications
from cartography.intel.entra.applications import sync_entra_applications
from cartography.intel.entra.applications import transform_app_role_assignments
from cartography.intel.entra.applications import transform_applications
from cartography.models.entra.app_role_assignment import EntraAppRoleAssignmentSchema
from cartography.models.entra.application import EntraApplicationSchema
from tests.data.entra.applications import MOCK_APP_ROLE_ASSIGNMENTS
from tests.data.entra.applications import MOCK_ENTRA_APPLICATIONS


def test_transform_applications():
    result = transform_applications(MOCK_ENTRA_APPLICATIONS)
    assert len(result) == 2

    app1 = next(a for a in result if a["id"] == "11111111-1111-1111-1111-111111111111")
    assert app1["display_name"] == "Finance Tracker"
    assert app1["publisher_domain"] == "example.com"
    assert app1["sign_in_audience"] == "AzureADMyOrg"
    assert app1["app_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_transform_app_role_assignments():
    result = transform_app_role_assignments(MOCK_APP_ROLE_ASSIGNMENTS)
    assert len(result) == 4

    # Test user assignment
    assignment1 = next(a for a in result if a["id"] == "assignment-1")
    assert assignment1["principal_id"] == "ae4ac864-4433-4ba6-96a6-20f8cffdadcb"
    assert assignment1["principal_display_name"] == "Test User 1"
    assert assignment1["resource_display_name"] == "Finance Tracker"
    assert assignment1["principal_type"] == "User"

    # Test group assignment
    assignment3 = next(a for a in result if a["id"] == "assignment-3")
    assert assignment3["principal_id"] == "11111111-2222-3333-4444-555555555555"
    assert assignment3["principal_display_name"] == "Finance Team"
    assert assignment3["resource_display_name"] == "Finance Tracker"
    assert assignment3["principal_type"] == "Group"


@patch("cartography.intel.entra.applications.load")
def test_load_applications(mock_load):
    session = MagicMock()
    data = [{"id": "1"}]
    load_applications(session, data, 1, "tenant")
    mock_load.assert_called_with(
        session,
        EntraApplicationSchema(),
        data,
        lastupdated=1,
        TENANT_ID="tenant",
    )


@patch("cartography.intel.entra.applications.load")
def test_load_app_role_assignments(mock_load):
    session = MagicMock()
    data = [{"id": "1"}]
    load_app_role_assignments(session, data, 1, "tenant")
    mock_load.assert_called_with(
        session,
        EntraAppRoleAssignmentSchema(),
        data,
        lastupdated=1,
        TENANT_ID="tenant",
    )


@patch("cartography.intel.entra.applications.GraphJob")
def test_cleanup_applications(mock_graph_job):
    session = MagicMock()
    params = {"UPDATE_TAG": 1, "TENANT_ID": "tenant"}
    cleanup_applications(session, params)
    mock_graph_job.from_node_schema.assert_called_with(
        EntraApplicationSchema(),
        params,
    )
    mock_graph_job.from_node_schema.return_value.run.assert_called_with(session)


@patch("cartography.intel.entra.applications.GraphJob")
def test_cleanup_app_role_assignments(mock_graph_job):
    session = MagicMock()
    params = {"UPDATE_TAG": 1, "TENANT_ID": "tenant"}
    cleanup_app_role_assignments(session, params)
    mock_graph_job.from_node_schema.assert_called_with(
        EntraAppRoleAssignmentSchema(),
        params,
    )
    mock_graph_job.from_node_schema.return_value.run.assert_called_with(session)


@patch("cartography.intel.entra.applications.cleanup_app_role_assignments")
@patch("cartography.intel.entra.applications.load_app_role_assignments")
@patch("cartography.intel.entra.applications.cleanup_applications")
@patch("cartography.intel.entra.applications.load_applications")
@patch("cartography.intel.entra.applications.load_tenant")
@patch("cartography.intel.entra.applications.GraphServiceClient")
@patch("cartography.intel.entra.applications.ClientSecretCredential")
@patch(
    "cartography.intel.entra.applications.get_app_role_assignments",
    new_callable=AsyncMock,
    return_value=MOCK_APP_ROLE_ASSIGNMENTS,
)
@patch(
    "cartography.intel.entra.applications.get_entra_applications",
    new_callable=AsyncMock,
    return_value=MOCK_ENTRA_APPLICATIONS,
)
@pytest.mark.asyncio
async def test_sync_entra_applications(
    mock_get,
    mock_get_assignments,
    mock_cred,
    mock_graph,
    mock_load_tenant,
    mock_load_apps,
    mock_cleanup,
    mock_load_assignments,
    mock_cleanup_assignments,
):
    session = MagicMock()
    await sync_entra_applications(
        session,
        "tid",
        "cid",
        "sec",
        1,
        {"UPDATE_TAG": 1, "TENANT_ID": "tid"},
    )
    mock_cred.assert_called_with(
        tenant_id="tid",
        client_id="cid",
        client_secret="sec",
    )
    mock_graph.assert_called_with(
        mock_cred.return_value,
        scopes=["https://graph.microsoft.com/.default"],
    )
    mock_get.assert_called_with(mock_graph.return_value)
    mock_get_assignments.assert_called_with(
        mock_graph.return_value, MOCK_ENTRA_APPLICATIONS
    )

    expected_apps = transform_applications(MOCK_ENTRA_APPLICATIONS)
    expected_assignments = transform_app_role_assignments(MOCK_APP_ROLE_ASSIGNMENTS)

    mock_load_tenant.assert_called_with(session, {"id": "tid"}, 1)
    mock_load_apps.assert_called_with(session, expected_apps, 1, "tid")
    mock_load_assignments.assert_called_with(session, expected_assignments, 1, "tid")
    mock_cleanup.assert_called_with(session, {"UPDATE_TAG": 1, "TENANT_ID": "tid"})
    mock_cleanup_assignments.assert_called_with(
        session, {"UPDATE_TAG": 1, "TENANT_ID": "tid"}
    )
