from types import SimpleNamespace
from unittest.mock import patch

import cartography.intel.bitbucket.repositories
import cartography.intel.bitbucket.users
import cartography.intel.bitbucket.workspaces
from cartography.intel.bitbucket import start_bitbucket_ingestion
from tests.data.bitbucket.repositories import MOCK_REPOSITORIES
from tests.data.bitbucket.repositories import TEST_REPO_WITH_PROJECT_ID
from tests.data.bitbucket.repositories import TEST_REPO_WITHOUT_PROJECT_ID
from tests.data.bitbucket.users import MOCK_MEMBERS
from tests.data.bitbucket.workspaces import MOCK_WORKSPACE_RAW
from tests.integration.util import check_nodes

TEST_UPDATE_TAG_1 = 111111111
TEST_UPDATE_TAG_2 = 222222222


def _config(update_tag):
    return SimpleNamespace(
        bitbucket_auth_method="token",
        bitbucket_token="fake-token",
        bitbucket_oauth_client_id=None,
        bitbucket_oauth_client_secret=None,
        bitbucket_oauth_refresh_token=None,
        bitbucket_workspaces="my-workspace",
        update_tag=update_tag,
    )


def test_cleanup_removes_repo_dropped_from_a_later_sync(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    with (
        patch.object(
            cartography.intel.bitbucket.workspaces,
            "get_workspace",
            return_value=MOCK_WORKSPACE_RAW,
        ),
        patch.object(
            cartography.intel.bitbucket.repositories,
            "get_repositories",
            return_value=MOCK_REPOSITORIES["values"],
        ),
        patch("cartography.intel.bitbucket.projects.get_projects", return_value=[]),
        patch.object(
            cartography.intel.bitbucket.users,
            "get_workspace_members",
            return_value=MOCK_MEMBERS["values"],
        ),
    ):
        start_bitbucket_ingestion(neo4j_session, _config(TEST_UPDATE_TAG_1))

    assert check_nodes(neo4j_session, "BitbucketRepository", ["id"]) == {
        (TEST_REPO_WITH_PROJECT_ID,),
        (TEST_REPO_WITHOUT_PROJECT_ID,),
    }

    # Second sync drops one repo from the upstream API response.
    remaining_repo = [
        r for r in MOCK_REPOSITORIES["values"] if r["uuid"] != "{repo-uuid-2}"
    ]
    with (
        patch.object(
            cartography.intel.bitbucket.workspaces,
            "get_workspace",
            return_value=MOCK_WORKSPACE_RAW,
        ),
        patch.object(
            cartography.intel.bitbucket.repositories,
            "get_repositories",
            return_value=remaining_repo,
        ),
        patch("cartography.intel.bitbucket.projects.get_projects", return_value=[]),
        patch.object(
            cartography.intel.bitbucket.users,
            "get_workspace_members",
            return_value=MOCK_MEMBERS["values"],
        ),
    ):
        start_bitbucket_ingestion(neo4j_session, _config(TEST_UPDATE_TAG_2))

    assert check_nodes(neo4j_session, "BitbucketRepository", ["id"]) == {
        (TEST_REPO_WITH_PROJECT_ID,),
    }
    # The workspace itself, synced both times, survives.
    assert len(check_nodes(neo4j_session, "BitbucketWorkspace", ["id"])) == 1
