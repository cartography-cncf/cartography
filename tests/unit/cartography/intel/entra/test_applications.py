from cartography.intel.entra.applications import transform_app_role_assignments
from cartography.intel.entra.applications import transform_applications
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
