from unittest.mock import Mock
from unittest.mock import patch

import requests

import cartography.intel.tailscale.devices
import tests.data.tailscale.devicepostureattributes
import tests.data.tailscale.devices
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.cartography.intel.tailscale.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


def _ensure_local_neo4j_has_test_devices(neo4j_session):
    """Helper function to populate Neo4j with test Tailscale devices."""
    # transform mutates device dicts in-place to add serial_number
    cartography.intel.tailscale.devices.transform(
        tests.data.tailscale.devices.TAILSCALE_DEVICES,
    )
    cartography.intel.tailscale.devices.load_devices(
        neo4j_session,
        tests.data.tailscale.devices.TAILSCALE_DEVICES,
        TEST_ORG,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_device_posture_attributes",
    return_value=tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES,
)
def test_load_tailscale_devices(mock_attrs, mock_api, neo4j_session):
    """
    Ensure that devices actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert Devices exist
    expected_nodes = {
        ("n292kg92CNTRL", "bluemarge-linux.tailfe8c.ts.net"),
        ("p892kg92CNTRL", "itchy-windows.tailfe8c.ts.net"),
        ("n2fskgfgCNT89", "donut-mac.tailfe8c.ts.net"),
        ("abcskgfgCN789", "anonymous-pixel.tailfe8c.ts.net"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleDevice", ["id", "name"]) == expected_nodes
    )

    # Using a direct query to assert Device properties because addresses is a unhashable list
    result = neo4j_session.run(
        "MATCH (n:TailscaleDevice) RETURN n.id AS id, n.addresses AS addresses, n.serial_number AS serial_number",
    )
    expected = {
        ("abcskgfgCN789", (), "HACK-PIXEL-01"),
        ("p892kg92CNTRL", ("100.64.0.1", "fd7a:115c:a1e0::1"), None),
        ("n2fskgfgCNT89", ("100.64.0.2",), "SIMP-MAC-HOMER-01"),
        ("n292kg92CNTRL", (), None),
    }
    actual = {
        (r["id"], tuple(r["addresses"]) if r["addresses"] else (), r["serial_number"])
        for r in result
    }
    assert actual == expected

    result = neo4j_session.run(
        """
        MATCH (n:TailscaleDevice)
        RETURN
            n.id AS id,
            n.posture_node_os AS posture_node_os,
            n.posture_sentinelone_infected AS posture_sentinelone_infected,
            n.posture_falcon_zta_score AS posture_falcon_zta_score,
            n.posture_intune_compliance_state AS posture_intune_compliance_state,
            n.posture_intune_managed_device_owner_type AS posture_intune_managed_device_owner_type
        """,
    )
    expected = {
        ("abcskgfgCN789", "android", True, None, None, None),
        ("p892kg92CNTRL", "windows", True, 85, None, None),
        ("n2fskgfgCNT89", "macos", False, None, "compliant", "company"),
        ("n292kg92CNTRL", "linux", False, None, None, None),
    }
    actual = {
        (
            r["id"],
            r["posture_node_os"],
            r["posture_sentinelone_infected"],
            r["posture_falcon_zta_score"],
            r["posture_intune_compliance_state"],
            r["posture_intune_managed_device_owner_type"],
        )
        for r in result
    }
    assert actual == expected

    # Assert Devices are connected with Tailnet
    expected_rels = {
        ("n292kg92CNTRL", TEST_ORG),
        ("n2fskgfgCNT89", TEST_ORG),
        ("p892kg92CNTRL", TEST_ORG),
        ("abcskgfgCN789", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevice",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Users are connected with Devices
    expected_rels = {
        ("123456", "n292kg92CNTRL"),
        ("123456", "p892kg92CNTRL"),
        ("654321", "n2fskgfgCNT89"),
        ("654321", "abcskgfgCN789"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleDevice",
            "id",
            "OWNS",
            rel_direction_right=True,
        )
        == expected_rels
    )


def test_get_device_posture_attributes_handles_scalar_and_object_values():
    api_session = Mock()
    response = Mock()
    response.json.return_value = {
        "attributes": {
            "sentinelOne:infected": "true",
            "falcon:ztaScore": {"value": "85"},
            "intune:complianceState": {"value": "compliant"},
            "fleet:present": True,
        },
    }
    response.raise_for_status.return_value = None
    api_session.get.return_value = response

    devices = [
        {
            "nodeId": "device-1",
            "os": "linux",
            "clientVersion": "v1.80.0",
        },
    ]

    results = cartography.intel.tailscale.devices.get_device_posture_attributes(
        api_session,
        "https://fake.tailscale.com",
        devices,
    )

    assert results == {
        "device-1": {
            "node:os": "linux",
            "node:tsVersion": "1.80.0",
            "sentinelOne:infected": True,
            "falcon:ztaScore": 85,
            "intune:complianceState": "compliant",
            "fleet:present": True,
        },
    }
