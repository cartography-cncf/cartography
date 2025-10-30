from unittest.mock import patch

import cartography.intel.googleworkspace.devices
from cartography.intel.googleworkspace.devices import sync_googleworkspace_devices
from tests.data.googleworkspace.devices import MOCK_DEVICES_RESPONSE
from tests.data.googleworkspace.devices import MOCK_DEVICE_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = "C01234567"


@patch.object(cartography.intel.googleworkspace.devices, "get_device_users", return_value=MOCK_DEVICE_USERS_RESPONSE)
@patch.object(cartography.intel.googleworkspace.devices, "get_devices", return_value=MOCK_DEVICES_RESPONSE)
def test_sync_googleworkspace_devices(_mock_get_devices, _mock_get_device_users, neo4j_session):
    """
    Test that Google Workspace devices sync correctly and create proper nodes and relationships
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    
    # Act
    sync_googleworkspace_devices(
        neo4j_session,
        creds=None,  # Mocked
        admin_email=None,
        customer_id=TEST_CUSTOMER_ID,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify devices are created
    expected_devices = {
        ("devices/EiRlNzYzZjYyNC1lNWMyLTQ3NmItODI4Yi03ZThiMGIyNjVjZjM%3D", "ANDROID", "3aac7e1206db9d26"),
        ("devices/EiQ4Mzk2Y2YxMS1lODhjLTRhM2ItYmQ1Zi1kZWYwMjQ2NTdhNGU%3D", "MAC_OS", "8396cf11-e88c-4a3b-bd5f-def024657a4e"),
    }
    assert check_nodes(neo4j_session, "GoogleWorkspaceDevice", ["id", "deviceType", "deviceId"]) == expected_devices

    # Assert - Verify user-device relationships are created
    expected_user_device_rels = {
        ("dana.dinesh@goodenoughlabs.ai", "devices/EiRlNzYzZjYyNC1lNWMyLTQ3NmItODI4Yi03ZThiMGIyNjVjZjM%3D"),
        ("gil.fowler@goodenoughlabs.ai", "devices/EiQ4Mzk2Y2YxMS1lODhjLTRhM2ItYmQ1Zi1kZWYwMjQ2NTdhNGU%3D"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceUser",
            "email",
            "GoogleWorkspaceDevice",
            "name", 
            "OWNS",
            rel_direction_right=True,
        )
        == expected_user_device_rels
    )

    # Assert - Verify tenant was created and devices are connected to it
    expected_tenant_nodes = {
        (TEST_CUSTOMER_ID,),
    }
    assert check_nodes(neo4j_session, "GoogleWorkspaceTenant", ["id"]) == expected_tenant_nodes

    # Assert - Verify device to tenant relationships
    expected_device_tenant_rels = {
        ("devices/EiRlNzYzZjYyNC1lNWMyLTQ3NmItODI4Yi03ZThiMGIyNjVjZjM%3D", TEST_CUSTOMER_ID),
        ("devices/EiQ4Mzk2Y2YxMS1lODhjLTRhM2ItYmQ1Zi1kZWYwMjQ2NTdhNGU%3D", TEST_CUSTOMER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceDevice",
            "id",
            "GoogleWorkspaceTenant",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_device_tenant_rels
    )

