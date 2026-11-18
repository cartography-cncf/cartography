from unittest.mock import patch

import cartography.intel.bitbucket.users
from cartography.intel.bitbucket.auth import BearerTokenCredential
from cartography.intel.bitbucket.workspaces import load_workspaces
from tests.data.bitbucket.users import MOCK_MEMBERS
from tests.data.bitbucket.users import TEST_USER_ACCOUNT_ID
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_ID
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_SLUG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.bitbucket.users,
    "get_workspace_members",
    return_value=MOCK_MEMBERS["values"],
)
def test_sync_users(mock_get, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    load_workspaces(
        neo4j_session,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
        TEST_UPDATE_TAG,
    )

    skipped = cartography.intel.bitbucket.users.sync_bitbucket_users(
        neo4j_session,
        BearerTokenCredential("fake-token"),
        TEST_UPDATE_TAG,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
    )

    mock_get.assert_called_once()
    assert mock_get.call_args.args[1] == TEST_WORKSPACE_SLUG
    assert skipped == set()
    assert check_nodes(neo4j_session, "BitbucketUser", ["id"]) == {
        (TEST_USER_ACCOUNT_ID,),
    }

    user_account_labels = neo4j_session.run(
        "MATCH (u:BitbucketUser:UserAccount) RETURN count(u) AS c",
    ).single()
    assert user_account_labels["c"] == 1

    assert check_rels(
        neo4j_session,
        "BitbucketWorkspace",
        "id",
        "BitbucketUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_WORKSPACE_ID, TEST_USER_ACCOUNT_ID)}
