from unittest.mock import patch

import cartography.intel.bitbucket.repositories
from cartography.intel.bitbucket.auth import BearerTokenCredential
from cartography.intel.bitbucket.projects import load_projects
from cartography.intel.bitbucket.workspaces import load_workspaces
from tests.data.bitbucket.projects import TEST_PROJECT_ID
from tests.data.bitbucket.projects import TEST_PROJECT_KEY
from tests.data.bitbucket.repositories import MOCK_REPOSITORIES
from tests.data.bitbucket.repositories import TEST_REPO_WITH_PROJECT_ID
from tests.data.bitbucket.repositories import TEST_REPO_WITHOUT_PROJECT_ID
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_ID
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_SLUG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_workspace_and_project(neo4j_session):
    load_workspaces(
        neo4j_session,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
        TEST_UPDATE_TAG,
    )
    load_projects(
        neo4j_session,
        [{"id": TEST_PROJECT_ID, "key": TEST_PROJECT_KEY}],
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.bitbucket.repositories,
    "get_repositories",
    return_value=MOCK_REPOSITORIES["values"],
)
def test_sync_repositories(mock_get, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_project(neo4j_session)

    cartography.intel.bitbucket.repositories.sync_bitbucket_repositories(
        neo4j_session,
        BearerTokenCredential("fake-token"),
        TEST_UPDATE_TAG,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
    )

    assert check_nodes(neo4j_session, "BitbucketRepository", ["id"]) == {
        (TEST_REPO_WITH_PROJECT_ID,),
        (TEST_REPO_WITHOUT_PROJECT_ID,),
    }
    assert check_nodes(neo4j_session, "CodeRepository", ["id"]) == {
        (TEST_REPO_WITH_PROJECT_ID,),
        (TEST_REPO_WITHOUT_PROJECT_ID,),
    }

    assert check_rels(
        neo4j_session,
        "BitbucketWorkspace",
        "id",
        "BitbucketRepository",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_WORKSPACE_ID, TEST_REPO_WITH_PROJECT_ID),
        (TEST_WORKSPACE_ID, TEST_REPO_WITHOUT_PROJECT_ID),
    }

    # Only the repo with a project gets a CONTAINS edge.
    assert check_rels(
        neo4j_session,
        "BitbucketProject",
        "id",
        "BitbucketRepository",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(TEST_PROJECT_ID, TEST_REPO_WITH_PROJECT_ID)}
