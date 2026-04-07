from unittest.mock import patch

import requests

import cartography.intel.jumpcloud.applications
import cartography.intel.jumpcloud.tenant
import tests.data.jumpcloud.applications
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "jumpcloud-org-abc123"


@patch.object(
    cartography.intel.jumpcloud.applications,
    "get",
    return_value=tests.data.jumpcloud.applications.JUMPCLOUD_APPLICATIONS,
)
def test_sync_jumpcloud_applications(mock_api, neo4j_session):
    """
    Ensure that JumpCloud applications are loaded with correct nodes and relationships.
    """
    query = """
    UNWIND $users AS user
    MERGE (u:JumpCloudUser {id: user.id})
    SET u.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        users=[
            {"id": "aabbccdd001122334455667701"},
            {"id": "aabbccdd001122334455667702"},
        ],
        UpdateTag=TEST_UPDATE_TAG,
    )

    cartography.intel.jumpcloud.tenant.sync(neo4j_session, TEST_ORG_ID, TEST_UPDATE_TAG)
    cartography.intel.jumpcloud.applications.sync(
        neo4j_session,
        requests.Session(),
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID},
    )

    assert check_nodes(neo4j_session, "JumpCloudTenant", ["id"]) == {(TEST_ORG_ID,)}

    expected_app_nodes = {
        ("jc-app-001", "google-workspace"),
        ("jc-app-002", "atlassian"),
    }
    assert (
        check_nodes(neo4j_session, "JumpCloudSaaSApplication", ["id", "name"])
        == expected_app_nodes
    )

    expected_tenant_rels = {
        ("jc-app-001", TEST_ORG_ID),
        ("jc-app-002", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "JumpCloudSaaSApplication",
            "id",
            "JumpCloudTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_tenant_rels
    )

    expected_user_rels = {
        ("jc-app-001", "aabbccdd001122334455667702"),
        ("jc-app-002", "aabbccdd001122334455667702"),
    }
    assert (
        check_rels(
            neo4j_session,
            "JumpCloudSaaSApplication",
            "id",
            "JumpCloudUser",
            "id",
            "USES",
            rel_direction_right=False,
        )
        == expected_user_rels
    )
