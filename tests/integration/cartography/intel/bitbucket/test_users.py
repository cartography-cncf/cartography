from types import SimpleNamespace
from unittest.mock import patch

import requests

import cartography.intel.bitbucket.users
from cartography.intel.bitbucket import start_bitbucket_ingestion
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


def _member(account_id):
    return {"user": {"account_id": account_id, "display_name": account_id}}


def _forbidden():
    response = requests.Response()
    response.status_code = 403
    return requests.exceptions.HTTPError(response=response)


def _sync_two_workspaces(neo4j_session, update_tag, members_by_slug):
    def get_members(_credential, slug):
        members = members_by_slug[slug]
        if isinstance(members, Exception):
            raise members
        return members

    config = SimpleNamespace(
        bitbucket_auth_method="token",
        bitbucket_token="fake-token",
        bitbucket_oauth_client_id=None,
        bitbucket_oauth_client_secret=None,
        bitbucket_oauth_refresh_token=None,
        bitbucket_workspaces="ws-a,ws-b",
        update_tag=update_tag,
    )
    with (
        patch(
            "cartography.intel.bitbucket.workspaces.get_workspace",
            side_effect=lambda _credential, slug: {"uuid": f"{{{slug}}}", "slug": slug},
        ),
        patch("cartography.intel.bitbucket.projects.get_projects", return_value=[]),
        patch(
            "cartography.intel.bitbucket.repositories.get_repositories",
            return_value=[],
        ),
        patch.object(
            cartography.intel.bitbucket.users,
            "get_workspace_members",
            side_effect=get_members,
        ),
    ):
        start_bitbucket_ingestion(neo4j_session, config)


def test_user_shared_with_unreadable_workspace_survives_cleanup(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_two_workspaces(
        neo4j_session,
        1,
        {"ws-a": [_member("alice"), _member("bob")], "ws-b": [_member("alice")]},
    )

    # Alice leaves ws-a, and ws-b's members can't be listed this run.
    _sync_two_workspaces(
        neo4j_session,
        2,
        {"ws-a": [_member("bob")], "ws-b": _forbidden()},
    )

    assert check_rels(
        neo4j_session,
        "BitbucketWorkspace",
        "id",
        "BitbucketUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("ws-a", "alice"), ("ws-a", "bob"), ("ws-b", "alice")}
