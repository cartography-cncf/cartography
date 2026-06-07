from unittest.mock import patch

import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.postureresolution
import tests.data.tailscale.acls
import tests.data.tailscale.devicepostureattributes
import tests.data.tailscale.devices
import tests.data.tailscale.postureintegrations
import tests.data.tailscale.users
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.cartography.intel.tailscale.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.acls.TAILSCALE_ACL_FILE,
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
@patch.object(
    cartography.intel.tailscale.postureintegrations,
    "get",
    return_value=tests.data.tailscale.postureintegrations.TAILSCALE_POSTUREINTEGRATIONS,
)
def test_resolve_tailscale_device_posture_compliance(
    mock_integrations,
    mock_attrs,
    mock_devices,
    mock_acls,
    neo4j_session,
):
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    _, device_posture_attributes = cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )
    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )
    postures, posture_conditions, _, _ = cartography.intel.tailscale.acls.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
        tests.data.tailscale.users.TAILSCALE_USERS,
    )

    cartography.intel.tailscale.postureresolution.sync(
        neo4j_session,
        org=TEST_ORG,
        update_tag=TEST_UPDATE_TAG,
        postures=postures,
        posture_conditions=posture_conditions,
        device_posture_attributes=device_posture_attributes,
    )

    expected_condition_rels = {
        ("n292kg92CNTRL", "posture:healthySentinelOne:0"),
        ("n292kg92CNTRL", "posture:healthySentinelOneMac:1"),
        ("n2fskgfgCNT89", "posture:healthySentinelOne:0"),
        ("n2fskgfgCNT89", "posture:healthySentinelOneMac:0"),
        ("n2fskgfgCNT89", "posture:healthySentinelOneMac:1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevice",
            "id",
            "TailscaleDevicePostureCondition",
            "id",
            "CONFORMS_TO",
            rel_direction_right=True,
        )
        == expected_condition_rels
    )

    expected_posture_rels = {
        ("n292kg92CNTRL", "posture:healthySentinelOne"),
        ("n2fskgfgCNT89", "posture:healthySentinelOne"),
        ("n2fskgfgCNT89", "posture:healthySentinelOneMac"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevice",
            "id",
            "TailscaleDevicePosture",
            "id",
            "CONFORMS_TO",
            rel_direction_right=True,
        )
        == expected_posture_rels
    )
