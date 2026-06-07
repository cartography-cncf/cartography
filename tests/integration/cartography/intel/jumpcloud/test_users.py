from unittest.mock import patch

import requests

import cartography.intel.jumpcloud.tenant
import cartography.intel.jumpcloud.users
import tests.data.jumpcloud.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "jumpcloud-org-abc123"


@patch.object(
    cartography.intel.jumpcloud.users,
    "get",
    return_value=tests.data.jumpcloud.users.JUMPCLOUD_USERS,
)
def test_sync_jumpcloud_users(mock_api, neo4j_session):
    """
    Ensure that JumpCloud users are loaded with correct nodes and relationships.
    """
    # Act
    cartography.intel.jumpcloud.tenant.sync(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)
    cartography.intel.jumpcloud.users.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID},
    )

    # Assert tenant exists
    assert check_nodes(neo4j_session, "JumpCloudTenant", ["id"]) == {(TEST_ORG_ID,)}

    # Assert users exist
    expected_users = {
        ("aabbccdd001122334455667701", "mbsimpson@simpson.corp"),
        ("aabbccdd001122334455667702", "hjsimpson@simpson.corp"),
    }
    assert (
        check_nodes(neo4j_session, "JumpCloudUser", ["id", "email"]) == expected_users
    )

    # Assert tenant -> user RESOURCE relationships
    expected_tenant_rels = {
        ("aabbccdd001122334455667701", TEST_ORG_ID),
        ("aabbccdd001122334455667702", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "JumpCloudUser",
            "id",
            "JumpCloudTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_tenant_rels
    )
