from unittest.mock import patch

import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.postureintegrations
import tests.data.tailscale.acls
import tests.data.tailscale.postureintegrations
import tests.data.tailscale.users
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


@patch.object(
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.acls.TAILSCALE_ACL_FILE,
)
@patch.object(
    cartography.intel.tailscale.postureintegrations,
    "get",
    return_value=tests.data.tailscale.postureintegrations.TAILSCALE_POSTUREINTEGRATIONS,
)
def test_load_tailscale_device_postures(mock_integrations, mock_api, neo4j_session):
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    cartography.intel.tailscale.acls.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
        tests.data.tailscale.users.TAILSCALE_USERS,
    )

    expected_postures = {
        ("posture:healthySentinelOne", "healthySentinelOne"),
        ("posture:healthySentinelOneMac", "healthySentinelOneMac"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleDevicePosture", ["id", "name"])
        == expected_postures
    )

    expected_conditions = {
        (
            "posture:healthySentinelOne:0",
            "sentinelOne:infected",
            "sentinelone",
            "==",
            "false",
        ),
        ("posture:healthySentinelOneMac:0", "node:os", "node", "==", "macos"),
        (
            "posture:healthySentinelOneMac:1",
            "sentinelOne:infected",
            "sentinelone",
            "==",
            "false",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "TailscaleDevicePostureCondition",
            ["id", "name", "provider", "operator", "value"],
        )
        == expected_conditions
    )

    expected_resource_rels = {
        ("posture:healthySentinelOne", TEST_ORG),
        ("posture:healthySentinelOneMac", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevicePosture",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_resource_rels
    )

    expected_condition_rels = {
        ("posture:healthySentinelOne", "posture:healthySentinelOne:0"),
        ("posture:healthySentinelOneMac", "posture:healthySentinelOneMac:0"),
        ("posture:healthySentinelOneMac", "posture:healthySentinelOneMac:1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevicePosture",
            "id",
            "TailscaleDevicePostureCondition",
            "id",
            "HAS_CONDITION",
            rel_direction_right=True,
        )
        == expected_condition_rels
    )

    expected_requires_rels = {
        ("posture:healthySentinelOne:0", "pcBEPQVMpki7S1"),
        ("posture:healthySentinelOneMac:1", "pcBEPQVMpki7S1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleDevicePostureCondition",
            "id",
            "TailscalePostureIntegration",
            "id",
            "REQUIRES",
            rel_direction_right=True,
        )
        == expected_requires_rels
    )
