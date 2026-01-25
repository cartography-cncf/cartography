from unittest.mock import patch

import requests

import cartography.intel.tailscale.devices
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
def test_load_tailscale_devices(mock_api, neo4j_session):
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
        "MATCH (n:TailscaleDevice) RETURN n.id AS id, n.addresses AS addresses",
    )
    expected_addresses = {
        ("abcskgfgCN789", ()),
        ("p892kg92CNTRL", ("100.64.0.1", "fd7a:115c:a1e0::1")),
        ("n2fskgfgCNT89", ("100.64.0.2",)),
        ("n292kg92CNTRL", ()),
    }
    actual_addresses = {
        (r["id"], tuple(r["addresses"]) if r["addresses"] else ()) for r in result
    }
    assert actual_addresses == expected_addresses

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
