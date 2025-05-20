from unittest.mock import patch

import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.users
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
def test_load_tailscale_groups(mock_api, neo4j_session):
    """
    Ensure that groups actually get loaded
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
    cartography.intel.tailscale.acls.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
        tests.data.tailscale.users.TAILSCALE_USERS,
    )

    # Assert Groups exist
    expected_nodes = {
        ("autogroup:admin", "admin"),
        ("autogroup:member", "member"),
        ("autogroup:owner", "owner"),
        ("group:corp", "corp"),
        ("group:employees", "employees"),
        ("group:example", "example"),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleGroup", ["id", "name"]) == expected_nodes
    )

    # Assert Group to Tailnet relationships exist
    expected_rels = {
        ("group:corp", TEST_ORG),
        ("group:example", TEST_ORG),
        ("autogroup:member", TEST_ORG),
        ("autogroup:owner", TEST_ORG),
        ("autogroup:admin", TEST_ORG),
        ("group:employees", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Group to User relationships exist
    expected_rels = {
        ("autogroup:admin", "123456"),
        ("autogroup:member", "654321"),
        ("group:example", "654321"),
        ("autogroup:member", "123456"),
        ("autogroup:owner", "123456"),
        ("group:corp", "123456"),
        ("group:corp", "654321"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleUser",
            "id",
            "MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Group to Group relationships exist
    expected_rels = {
        ("group:employees", "group:corp"),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscaleGroup",
            "id",
            "TailscaleGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )
