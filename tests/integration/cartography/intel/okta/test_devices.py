from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from okta.models.device_list import DeviceList

import cartography.intel.okta.devices
import cartography.intel.ontology.devices
from tests.data.okta.devices import DEVICES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


@patch.object(
    cartography.intel.okta.devices,
    "_get_okta_devices",
    new_callable=AsyncMock,
)
def test_sync_okta_devices(mock_get_devices, neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    mock_get_devices.return_value = [
        DeviceList.model_validate(device) for device in DEVICES
    ]
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(user:OktaUser {id: 'user-001'})
        SET user.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(stale:OktaDevice {id: 'stale-device'})
        SET stale.lastupdated = 1
        MERGE (user)-[owns:OWNS]->(stale)
        SET owns.lastupdated = 1,
            owns._sub_resource_label = 'OktaOrganization',
            owns._sub_resource_id = $org_id
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.okta.devices.sync_okta_devices(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OktaDevice",
        ["id", "display_name", "serial_number", "status"],
    ) == {
        ("device-001", "Work MacBook", "SERIAL-001", "ACTIVE"),
        ("device-002", "Unassigned Windows Device", "SERIAL-002", "SUSPENDED"),
    }
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaDevice",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ORG_ID, "device-001"),
        (TEST_ORG_ID, "device-002"),
    }
    assert check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaDevice",
        "id",
        "OWNS",
        rel_direction_right=True,
    ) == {("user-001", "device-001")}

    relationship = neo4j_session.run(
        """
        MATCH (:OktaUser {id: 'user-001'})-[r:OWNS]->
              (:OktaDevice {id: 'device-001'})
        RETURN r.management_status AS management_status,
               r.screen_lock_type AS screen_lock_type,
               r.enrolled_at AS enrolled_at
        """,
    ).single()
    assert dict(relationship) == {
        "management_status": "MANAGED",
        "screen_lock_type": "BIOMETRIC",
        "enrolled_at": "2025-01-16T10:30:00Z",
    }


@patch.object(
    cartography.intel.okta.devices,
    "_get_okta_devices",
    new_callable=AsyncMock,
)
def test_okta_device_ontology_links(mock_get_devices, neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    mock_get_devices.return_value = [DeviceList.model_validate(DEVICES[0])]
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(account:OktaUser {id: 'user-001'})
        SET account.lastupdated = $update_tag
        MERGE (user:User {id: 'alice@example.com'})
        MERGE (user)-[:HAS_ACCOUNT]->(account)
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.okta.devices.sync_okta_devices(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Act
    cartography.intel.ontology.devices.sync(
        neo4j_session,
        ["okta"],
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "Device",
        ["hostname", "serial_number", "model"],
    ) == {("Work MacBook", "SERIAL-001", "MacBook Pro")}
    assert check_rels(
        neo4j_session,
        "Device",
        "serial_number",
        "OktaDevice",
        "serial_number",
        "OBSERVED_AS",
        rel_direction_right=True,
    ) == {("SERIAL-001", "SERIAL-001")}
    assert check_rels(
        neo4j_session,
        "User",
        "id",
        "Device",
        "serial_number",
        "OWNS",
        rel_direction_right=True,
    ) == {("alice@example.com", "SERIAL-001")}
