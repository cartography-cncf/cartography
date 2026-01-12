from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.devices
from tests.data.okta.devices import SAMPLE_DEVICES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.devices, "_create_device_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices(mock_get_devices, mock_device_client, neo4j_session):
    """
    Test that Okta devices are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Use sample devices from test data
    mock_get_devices.return_value = SAMPLE_DEVICES
    mock_device_client.return_value = MagicMock()

    # Create the OktaOrganization node first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Act - Call the main sync function
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify devices were created with correct properties
    expected_devices = {
        ("guo4a5u7YAHhjXrMK0g4", "Example device name 1", "WINDOWS", "CREATED"),
        ("guo4a5u7YAHhjXrMK0g5", "Example device name 2", "ANDROID", "ACTIVE"),
    }
    actual_devices = check_nodes(
        neo4j_session, "OktaDevice", ["id", "display_name", "platform", "status"]
    )
    assert actual_devices == expected_devices

    # Assert - Verify devices are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "guo4a5u7YAHhjXrMK0g4"),
        (TEST_ORG_ID, "guo4a5u7YAHhjXrMK0g5"),
    }
    actual_org_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaDevice",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_rels == expected_org_rels


@patch.object(cartography.intel.okta.devices, "_create_device_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices_with_user_relationships(
    mock_get_devices, mock_device_client, neo4j_session
):
    """
    Test that user-device relationships are created correctly.
    """
    # Arrange
    mock_get_devices.return_value = SAMPLE_DEVICES
    mock_device_client.return_value = MagicMock()

    # Create OktaOrganization
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create OktaUser that exists in the _embedded.users data
    neo4j_session.run(
        """
        MERGE (u:OktaUser{id: '00u17vh0q8ov8IU881d7'})
        SET u.email = 'email@email.com',
            u.lastupdated = $UPDATE_TAG
        """,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify user-device relationship exists
    expected_user_device_rels = {
        ("00u17vh0q8ov8IU881d7", "guo4a5u7YAHhjXrMK0g5"),
    }
    actual_user_device_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaDevice",
        "id",
        "HAS_DEVICE",
        rel_direction_right=True,
    )
    assert actual_user_device_rels == expected_user_device_rels

    # Assert - Verify relationship properties are stored
    result = neo4j_session.run(
        """
        MATCH (:OktaUser{id: '00u17vh0q8ov8IU881d7'})-[r:HAS_DEVICE]->(:OktaDevice{id: 'guo4a5u7YAHhjXrMK0g5'})
        RETURN r.management_status as mgmt_status, r.screen_lock_type as lock_type
        """,
    )
    rel_data = [dict(r) for r in result][0]
    assert rel_data["mgmt_status"] == "MANAGED"
    assert rel_data["lock_type"] == "BIOMETRIC"


@patch.object(cartography.intel.okta.devices, "_create_device_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices_device_properties(
    mock_get_devices, mock_device_client, neo4j_session
):
    """
    Test that device properties are stored correctly.
    """
    # Arrange
    mock_get_devices.return_value = SAMPLE_DEVICES
    mock_device_client.return_value = MagicMock()

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Check Windows device properties
    result = neo4j_session.run(
        """
        MATCH (d:OktaDevice{id: 'guo4a5u7YAHhjXrMK0g4'})
        RETURN d.display_name as name,
               d.platform as platform,
               d.serial_number as serial,
               d.sid as sid,
               d.registered as registered,
               d.secure_hardware_present as secure_hw,
               d.disk_encryption_type as encryption
        """,
    )
    device_data = [dict(r) for r in result][0]
    assert device_data["name"] == "Example device name 1"
    assert device_data["platform"] == "WINDOWS"
    assert device_data["serial"] == "XXDDRFCFRGF3M8MD6D"
    assert device_data["sid"] == "S-1-11-111"
    assert device_data["registered"] is True
    assert device_data["secure_hw"] is False
    assert device_data["encryption"] == "ALL_INTERNAL_VOLUMES"

    # Assert - Check Android device properties
    result = neo4j_session.run(
        """
        MATCH (d:OktaDevice{id: 'guo4a5u7YAHhjXrMK0g5'})
        RETURN d.display_name as name,
               d.platform as platform,
               d.manufacturer as manufacturer,
               d.model as model,
               d.os_version as os_version,
               d.secure_hardware_present as secure_hw,
               d.disk_encryption_type as encryption
        """,
    )
    device_data = [dict(r) for r in result][0]
    assert device_data["name"] == "Example device name 2"
    assert device_data["platform"] == "ANDROID"
    assert device_data["manufacturer"] == "Google"
    assert device_data["model"] == "Pixel 6"
    assert device_data["os_version"] == "13:2023-05-05"
    assert device_data["secure_hw"] is True
    assert device_data["encryption"] == "USER"


@patch.object(cartography.intel.okta.devices, "_create_device_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices_updates_existing(
    mock_get_devices, mock_device_client, neo4j_session
):
    """
    Test that syncing updates existing devices rather than creating duplicates.
    """
    # Arrange - Create an existing device in the graph
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(d:OktaDevice{id: 'guo4a5u7YAHhjXrMK0g4'})
        SET d.display_name = 'Old Device Name',
            d.status = 'DEACTIVATED',
            d.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated device data
    mock_get_devices.return_value = SAMPLE_DEVICES
    mock_device_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Device should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (d:OktaDevice{id: 'guo4a5u7YAHhjXrMK0g4'})
        RETURN d.display_name as name,
               d.status as status,
               d.lastupdated as lastupdated
        """,
    )
    devices = [dict(r) for r in result]
    assert len(devices) == 1  # Should be only one device, not a duplicate
    device_data = devices[0]
    assert device_data["name"] == "Example device name 1"
    assert device_data["status"] == "CREATED"
    assert device_data["lastupdated"] == TEST_UPDATE_TAG


@patch.object(cartography.intel.okta.devices, "_create_device_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices_optional_fields(
    mock_get_devices, mock_device_client, neo4j_session
):
    """
    Test that devices with missing optional fields are handled correctly.
    """
    # Arrange - Create a device with minimal fields
    minimal_device = {
        "id": "dev-minimal-001",
        "status": "CREATED",
        "created": "2024-12-19T00:00:00.000Z",
        "lastUpdated": "2024-12-19T00:00:00.000Z",
        "profile": {
            "displayName": "Minimal Device",
            "platform": "WINDOWS",
            "registered": False,
            # No manufacturer, model, serialNumber, etc.
        },
        "resourceType": "UDDevice",
        "resourceDisplayName": {
            "value": "Minimal Device",
            "sensitive": False,
        },
        "resourceAlternateId": None,
        "resourceId": "dev-minimal-001",
        "_links": {},
        "_embedded": {
            "users": [],
        },
    }

    mock_get_devices.return_value = [minimal_device]
    mock_device_client.return_value = MagicMock()

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Device should be created with null optional fields
    result = neo4j_session.run(
        """
        MATCH (d:OktaDevice{id: 'dev-minimal-001'})
        RETURN d.display_name as name,
               d.platform as platform,
               d.manufacturer as manufacturer,
               d.model as model,
               d.serial_number as serial,
               d.sid as sid
        """,
    )
    device_data = [dict(r) for r in result][0]
    assert device_data["name"] == "Minimal Device"
    assert device_data["platform"] == "WINDOWS"
    assert device_data["manufacturer"] is None
    assert device_data["model"] is None
    assert device_data["serial"] is None
    assert device_data["sid"] is None
