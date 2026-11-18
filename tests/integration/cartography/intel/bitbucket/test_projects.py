from unittest.mock import patch

import cartography.intel.bitbucket.projects
from cartography.intel.bitbucket.auth import BearerTokenCredential
from cartography.intel.bitbucket.workspaces import load_workspaces
from tests.data.bitbucket.projects import MOCK_PROJECTS
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_ID
from tests.data.bitbucket.workspaces import TEST_WORKSPACE_SLUG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_workspace(neo4j_session):
    load_workspaces(
        neo4j_session,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.bitbucket.projects,
    "get_projects",
    return_value=MOCK_PROJECTS["values"],
)
def test_sync_projects(mock_get, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace(neo4j_session)

    cartography.intel.bitbucket.projects.sync_bitbucket_projects(
        neo4j_session,
        BearerTokenCredential("fake-token"),
        TEST_UPDATE_TAG,
        [{"id": TEST_WORKSPACE_ID, "slug": TEST_WORKSPACE_SLUG}],
    )

    assert check_nodes(neo4j_session, "BitbucketProject", ["id", "key"]) == {
        ("project-uuid-1", "PROJ"),
    }

    assert check_rels(
        neo4j_session,
        "BitbucketWorkspace",
        "id",
        "BitbucketProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_WORKSPACE_ID, "project-uuid-1")}
