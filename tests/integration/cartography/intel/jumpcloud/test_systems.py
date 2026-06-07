from unittest.mock import patch

import requests

import cartography.intel.jumpcloud.systems
import tests.data.jumpcloud.systems
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "jumpcloud-org-abc123"


@patch.object(
    cartography.intel.jumpcloud.systems,
    "get",
    return_value=tests.data.jumpcloud.systems.JUMPCLOUD_SYSTEMS,
)
def test_sync_jumpcloud_systems(mock_api, neo4j_session):
    """
    Ensure that JumpCloud systems are loaded with correct nodes and relationships.
    """
    # Arrange: create JumpCloudUser nodes so the OWNS relationship can be formed
    query = """
    UNWIND $users AS user
    MERGE (u:JumpCloudUser {id: user.id})
    SET u.username = user.username, u.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        users=[
            {"id": "user-01", "username": "mbsimpson"},
            {"id": "user-02", "username": "hjsimpson"},
        ],
        UpdateTag=TEST_UPDATE_TAG,
    )

    cartography.intel.jumpcloud.systems.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID},
    )

    assert check_nodes(neo4j_session, "JumpCloudTenant", ["id"]) == {(TEST_ORG_ID,)}

    expected_system_nodes = {
        ("asset-01", "jc-system-01"),
        ("asset-02", "jc-system-02"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "JumpCloudSystem",
            ["id", "jc_system_id"],
        )
        == expected_system_nodes
    )

    expected_tenant_rels = {
        ("asset-01", TEST_ORG_ID),
        ("asset-02", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "JumpCloudSystem",
            "id",
            "JumpCloudTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_tenant_rels
    )

    expected_user_rels = {
        ("asset-01", "user-01"),
        ("asset-02", "user-02"),
    }
    assert (
        check_rels(
            neo4j_session,
            "JumpCloudSystem",
            "id",
            "JumpCloudUser",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_user_rels
    )
