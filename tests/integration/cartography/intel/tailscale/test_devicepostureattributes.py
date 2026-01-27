from unittest.mock import MagicMock
from unittest.mock import patch

import requests

import cartography.intel.tailscale.devices
import tests.data.tailscale.devices
import tests.data.tailscale.devicepostureattributes
from tests.integration.cartography.intel.tailscale.test_devices import (
    _ensure_local_neo4j_has_test_devices,
)
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


def _mock_get_posture_attributes(api_session, base_url, devices):
    """Return test posture attributes."""
    return tests.data.tailscale.devicepostureattributes.TAILSCALE_DEVICE_POSTURE_ATTRIBUTES


@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get_posture_attributes",
    side_effect=_mock_get_posture_attributes,
)
def test_load_tailscale_device_posture_attributes(mock_get_attributes, mock_get_devices, neo4j_session):
    """Test that device posture attributes are loaded correctly."""

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

    # Assert Posture Attributes exist
    expected_nodes = {
        ("p892kg92CNTRL:falcon:ztaScore", "falcon:ztaScore", "85"),
        ("p892kg92CNTRL:falcon:osVersion", "falcon:osVersion", "10.0.19045"),
        ("n2fskgfgCNT89:intune:complianceState", "intune:complianceState", "compliant"),
        ("n2fskgfgCNT89:intune:managedDeviceOwnerType", "intune:managedDeviceOwnerType", "company"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleDevicePostureAttribute", ["id", "key", "value"]) == expected_nodes
    )

    # Assert Posture Attributes are connected with Devices
    expected_rels = {
        ("p892kg92CNTRL", "p892kg92CNTRL:falcon:ztaScore"),
        ("p892kg92CNTRL", "p892kg92CNTRL:falcon:osVersion"),
        ("n2fskgfgCNT89", "n2fskgfgCNT89:intune:complianceState"),
        ("n2fskgfgCNT89", "n2fskgfgCNT89:intune:managedDeviceOwnerType"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevice",
            "id",
            "TailscaleDevicePostureAttribute",
            "id",
            "HAS_POSTURE_ATTRIBUTE",
            rel_direction_right=True,
        )
        == expected_rels
    )
