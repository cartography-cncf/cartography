from unittest.mock import patch

import cartography.intel.googleworkspace.devices
from cartography.intel.googleworkspace.devices import sync_googleworkspace_devices
from tests.data.googleworkspace.devices import MOCK_DEVICE_USERS_RESPONSE
from tests.data.googleworkspace.devices import MOCK_DEVICES_RESPONSE
from tests.integration.cartography.intel.googleworkspace.test_tenant import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.cartography.intel.googleworkspace.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = "ABC123CD"


@patch("cartography.intel.googleworkspace.devices.datetime")
@patch.object(
    cartography.intel.googleworkspace.devices,
    "get_devices",
    return_value=MOCK_DEVICES_RESPONSE,
)
@patch.object(
    cartography.intel.googleworkspace.devices,
    "get_device_users",
    return_value=MOCK_DEVICE_USERS_RESPONSE,
)
def test_sync_googleworkspace_devices(
    _mock_get_device_users,
    _mock_get_devices,
    mock_datetime_module,
    neo4j_session,
):
    """
    Test that Google Workspace devices sync correctly and create proper nodes and relationships
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Then sync devices
    sync_googleworkspace_devices(
        neo4j_session,
        cloudidentity=None,  # Mocked
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify devices are created
    expected_devices = {
        (
            "3aac7e1206db9d26",
            "ANDROID",
        ),
        (
            "8396cf11-e88c-4a3b-bd5f-def024657a4e",
            "MAC_OS",
        ),
    }
    assert (
        check_nodes(neo4j_session, "GoogleWorkspaceDevice", ["id", "device_type"])
        == expected_devices
    )

    # Assert - Verify user-device relationships are created
    expected_user_device_rels = {
        (
            "mbsimpson@simpson.corp",
            "3aac7e1206db9d26",
        ),
        (
            "hjsimpson@simpson.corp",
            "8396cf11-e88c-4a3b-bd5f-def024657a4e",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceUser",
            "primary_email",
            "GoogleWorkspaceDevice",
            "id",
            "OWNS",
            rel_direction_right=True,
        )
        == expected_user_device_rels
    )

    # Assert - Verify tenant was created and devices are connected to it
    expected_tenant_nodes = {
        (TEST_CUSTOMER_ID,),
    }
    assert (
        check_nodes(neo4j_session, "GoogleWorkspaceTenant", ["id"])
        == expected_tenant_nodes
    )

    # Assert - Verify device to tenant relationships
    expected_device_tenant_rels = {
        (
            "3aac7e1206db9d26",
            TEST_CUSTOMER_ID,
        ),
        (
            "8396cf11-e88c-4a3b-bd5f-def024657a4e",
            TEST_CUSTOMER_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceDevice",
            "id",
            "GoogleWorkspaceTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_device_tenant_rels
    )
