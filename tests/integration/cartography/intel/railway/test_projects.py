from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.railway.projects
import tests.data.railway.projects
import tests.data.railway.workspaces
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111"
TEST_PROJECT_ID = "33333333-3333-3333-3333-333333333333"
TEST_PUBLIC_PROJECT_ID = "34343434-3434-3434-3434-343434343434"


def _common_job_parameters(update_tag: int = TEST_UPDATE_TAG) -> dict:
    return {
        "UPDATE_TAG": update_tag,
        "BASE_URL": "https://backboard.railway.com/graphql/v2",
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
    }


def _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session):
    cartography.intel.railway.projects.load_workspace(
        neo4j_session,
        tests.data.railway.workspaces.RAILWAY_WORKSPACE,
        TEST_UPDATE_TAG,
    )
    cartography.intel.railway.projects.load_projects(
        neo4j_session,
        tests.data.railway.projects.RAILWAY_PROJECTS,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.railway.projects,
    "get_projects",
    return_value=tests.data.railway.projects.RAILWAY_PROJECTS,
)
@patch.object(
    cartography.intel.railway.projects,
    "get_workspace",
    return_value=tests.data.railway.workspaces.RAILWAY_WORKSPACE,
)
def test_load_railway_projects(mock_get_workspace, mock_get_projects, neo4j_session):
    # Act
    projects = cartography.intel.railway.projects.sync(
        neo4j_session,
        Mock(),
        _common_job_parameters(),
        TEST_UPDATE_TAG,
    )

    # Assert the workspace tenant exists
    assert check_nodes(neo4j_session, "RailwayWorkspace", ["id", "name", "plan"]) == {
        (TEST_WORKSPACE_ID, "Example Workspace", "HOBBY"),
    }

    # Assert projects exist, including the isPublic exposure flag
    assert check_nodes(
        neo4j_session,
        "RailwayProject",
        ["id", "name", "is_public"],
    ) == {
        (TEST_PROJECT_ID, "cartography-fixture", False),
        (TEST_PUBLIC_PROJECT_ID, "cartography-fixture-public", True),
    }

    # Assert projects are attached to the workspace
    assert check_rels(
        neo4j_session,
        "RailwayWorkspace",
        "id",
        "RailwayProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_WORKSPACE_ID, TEST_PROJECT_ID),
        (TEST_WORKSPACE_ID, TEST_PUBLIC_PROJECT_ID),
    }

    # Both tenant levels carry the ontology Tenant label
    assert check_nodes(neo4j_session, "Tenant", ["id"]) >= {
        (TEST_WORKSPACE_ID,),
        (TEST_PROJECT_ID,),
        (TEST_PUBLIC_PROJECT_ID,),
    }

    # sync() hands the project list back for the per-project fan-out
    assert [project["id"] for project in projects] == [
        TEST_PROJECT_ID,
        TEST_PUBLIC_PROJECT_ID,
    ]


@patch.object(
    cartography.intel.railway.projects,
    "get_workspace",
    return_value=tests.data.railway.workspaces.RAILWAY_WORKSPACE,
)
def test_railway_project_cleanup_removes_only_stale_projects(
    mock_get_workspace,
    neo4j_session,
):
    # Arrange: a first sync loads both projects.
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)

    # Act: re-sync with a newer update tag and only one project still present.
    surviving_project = tests.data.railway.projects.RAILWAY_PROJECTS[:1]
    with patch.object(
        cartography.intel.railway.projects,
        "get_projects",
        return_value=surviving_project,
    ):
        cartography.intel.railway.projects.sync(
            neo4j_session,
            Mock(),
            _common_job_parameters(TEST_UPDATE_TAG + 1),
            TEST_UPDATE_TAG + 1,
        )

    # Assert the project that vanished from the API is gone and the other survives.
    assert check_nodes(neo4j_session, "RailwayProject", ["id"]) == {
        (TEST_PROJECT_ID,),
    }
    # The workspace is a tenant node and is never cleaned up.
    assert check_nodes(neo4j_session, "RailwayWorkspace", ["id"]) == {
        (TEST_WORKSPACE_ID,),
    }
