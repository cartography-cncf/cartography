from unittest.mock import patch

import cartography.intel.bitbucket.workspaces
from cartography.intel.bitbucket.auth import BearerTokenCredential
from tests.data.bitbucket.workspaces import MOCK_WORKSPACE_RAW
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.bitbucket.workspaces,
    "get_workspace",
    return_value=MOCK_WORKSPACE_RAW,
)
def test_sync_workspaces_fetches_configured_slugs_directly(mock_get, neo4j_session):
    """
    Each configured workspace is looked up by name via get_workspace() - Bitbucket
    permanently removed the bare "list every workspace I can see" endpoint
    (CHANGE-2770), so a known slug is always required.
    """
    neo4j_session.run("MATCH (w:BitbucketWorkspace) DETACH DELETE w")
    cartography.intel.bitbucket.workspaces.sync_bitbucket_workspaces(
        neo4j_session,
        BearerTokenCredential("fake-token"),
        TEST_UPDATE_TAG,
        configured_slugs=["my-workspace"],
    )

    mock_get.assert_called_once_with(mock_get.call_args[0][0], "my-workspace")
    assert check_nodes(neo4j_session, "BitbucketWorkspace", ["id", "slug"]) == {
        ("workspace-uuid-1", "my-workspace"),
    }

    tenant_labels = neo4j_session.run(
        "MATCH (w:BitbucketWorkspace:Tenant) RETURN count(w) AS c",
    ).single()
    assert tenant_labels["c"] == 1
