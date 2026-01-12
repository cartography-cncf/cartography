from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.devices
from cartography.intel.okta.sync_state import OktaSyncState
from tests.data.okta.devices import create_test_device
from tests.data.okta.devices import create_test_device_no_user
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.devices, "create_api_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices(mock_get_devices, mock_api_client, neo4j_session):
    """
    Test that Okta devices are synced correctly to the graph.
    """
    # Arrange - Create test devices
    test_device_1 = create_test_device()
    test_device_2 = create_test_device()
    test_device_2["id"] = "device-002"
    test_device_2["profile"]["displayName"] = "MacBook Pro"
    test_device_2["_embedded"]["user"]["id"] = "user-002"

    # Mock the API calls
    mock_get_devices.return_value = [test_device_1, test_device_2]
    mock_api_client.return_value = MagicMock()

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

    # Create test users that devices will link to
    neo4j_session.run(
        """
        MERGE (u1:OktaUser{id: 'user-001'})
        SET u1.lastupdated = $UPDATE_TAG
        MERGE (u2:OktaUser{id: 'user-002'})
        SET u2.lastupdated = $UPDATE_TAG
        """,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sync_state = OktaSyncState()

    # Act - Call the main sync function
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Verify devices were created with correct properties
    expected_devices = {
        ("device-001", "ACTIVE", "iPhone 14 Pro"),
        ("device-002", "ACTIVE", "MacBook Pro"),
    }
    actual_devices = check_nodes(
        neo4j_session, "OktaDevice", ["id", "status", "display_name"]
    )
    assert actual_devices == expected_devices

    # Assert - Verify devices are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "device-001"),
        (TEST_ORG_ID, "device-002"),
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

    # Assert - Verify devices are connected to users via OWNS relationship
    expected_owns_rels = {
        ("user-001", "device-001"),
        ("user-002", "device-002"),
    }
    actual_owns_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaDevice",
        "id",
        "OWNS",
        rel_direction_right=True,
    )
    assert actual_owns_rels == expected_owns_rels


@patch.object(cartography.intel.okta.devices, "create_api_client")
@patch.object(cartography.intel.okta.devices, "_get_okta_devices")
def test_sync_okta_devices_no_user(
    mock_get_devices, mock_api_client, neo4j_session
):
    """
    Test that devices without user associations are handled correctly.
    """
    # Arrange
    test_device = create_test_device_no_user()

    mock_get_devices.return_value = [test_device]
    mock_api_client.return_value = MagicMock()

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sync_state = OktaSyncState()

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Device should be created but no OWNS relationship
    result = neo4j_session.run(
        """
        MATCH (d:OktaDevice{id: 'device-no-user'})
        RETURN d.id as id, d.user_id as user_id
        """,
    )
    devices = [dict(r) for r in result]
    assert len(devices) == 1
    assert devices[0]["id"] == "device-no-user"

    # Assert - No OWNS relationship should exist for device-no-user
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser)-[r:OWNS]->(d:OktaDevice{id: 'device-no-user'})
        RETURN u.id as user_id, d.id as device_id
        """,
    )
    relationships = [dict(r) for r in result]
    assert len(relationships) == 0, f"Found unexpected relationships: {relationships}"
