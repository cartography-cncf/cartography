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
        ("n292kg92CNTRL", "pangolin.tailfe8c.ts.net"),
        ("n2fskgfgCNT89", "monkey.tailfe8c.ts.net"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleDevice", ["id", "name"]) == expected_nodes
    )

    # Assert Devices are connected with Tailnet
    expected_rels = {
        ("n292kg92CNTRL", TEST_ORG),
        ("n2fskgfgCNT89", TEST_ORG),
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
        ("654321", "n2fskgfgCNT89"),
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
