from unittest.mock import patch

import requests

import cartography.intel.tailscale.users
import tests.data.tailscale.users
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.tailscale.users.load_users(
        neo4j_session,
        tests.data.tailscale.users.TAILSCALE_USERS,
        TEST_ORG,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.tailscale.users,
    "get",
    return_value=tests.data.tailscale.users.TAILSCALE_USERS,
)
def test_load_tailscale_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)

    # Act
    cartography.intel.tailscale.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert Users exist
    expected_nodes = {
        ("123456", "mbsimpson@simpson.corp"),
        ("654321", "hjsimpson@simpson.corp"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleUser", ["id", "login_name"])
        == expected_nodes
    )

    # Assert Users are connected with Tailnet
    expected_rels = {
        ("123456", TEST_ORG),
        ("654321", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleUser",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
