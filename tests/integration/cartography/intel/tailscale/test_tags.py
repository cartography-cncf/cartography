from unittest.mock import patch

import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import tests.data.tailscale.acls
import tests.data.tailscale.users
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
    cartography.intel.tailscale.acls,
    "get",
    return_value=tests.data.tailscale.acls.TAILSCALE_ACL_FILE,
)
@patch.object(
    cartography.intel.tailscale.devices,
    "get",
    return_value=tests.data.tailscale.devices.TAILSCALE_DEVICES,
)
def test_load_tailscale_tags(mock_devices, mock_acls, neo4j_session):
    """
    Ensure that tags actually get loaded
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

    # Act (tags are loaded both in ACL and devices)
    # so we need to call both sync functions
    cartography.intel.tailscale.acls.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
        tests.data.tailscale.users.TAILSCALE_USERS,
    )
    cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert Tags exist
    expected_nodes = {("tag:byod", "byod"), ("tag:compromized", "compromized")}
    assert check_nodes(neo4j_session, "TailscaleTag", ["id", "name"]) == expected_nodes

    # Assert Tag to Tailnet relationships exist
    expected_rels = {("tag:byod", TEST_ORG), ("tag:compromized", TEST_ORG)}
    assert (
        check_rels(
            neo4j_session,
            "TailscaleTag",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Group to Tag relationships exist
    expected_rels = {("autogroup:admin", "tag:byod")}
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleTag",
            "id",
            "OWNS",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert User to Tag relationships exist
    expected_rels = {
        ("654321", "tag:compromized"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleTag",
            "id",
            "OWNS",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert Tag to Device relationships exist
    expected_rels = {
        ("tag:byod", "p892kg92CNTRL"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleTag",
            "id",
            "TailscaleDevice",
            "id",
            "TAGGED",
            rel_direction_right=False,
        )
        == expected_rels
    )
