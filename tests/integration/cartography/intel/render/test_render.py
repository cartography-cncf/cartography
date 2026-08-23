from unittest.mock import patch

import cartography.intel.render
import cartography.intel.render.projects
import cartography.intel.render.tenants
from cartography.config import Config
from tests.data.render.data import OWNERS_RESPONSE
from tests.data.render.data import PROJECTS_RESPONSE
from tests.data.render.data import TEST_OWNER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_PROJECT_ID = "prj-test001"


@patch.object(
    cartography.intel.render.projects,
    "get",
    return_value=PROJECTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.tenants,
    "get",
    return_value=OWNERS_RESPONSE,
)
def test_start_render_ingestion(mock_get_owners, mock_get_projects, neo4j_session):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        render_api_key="test-api-key",
    )

    # Act
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(neo4j_session, "RenderTenant", ["id", "name"]) == {
        (TEST_OWNER_ID, "cartography-test-workspace"),
    }
    assert check_nodes(neo4j_session, "RenderProject", ["id", "name"]) == {
        (TEST_PROJECT_ID, "cartography-test-project"),
    }
    assert check_rels(
        neo4j_session,
        "RenderTenant",
        "id",
        "RenderProject",
        "id",
        "RESOURCE",
    ) == {
        (TEST_OWNER_ID, TEST_PROJECT_ID),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {
        (TEST_OWNER_ID,),
    }


@patch.object(
    cartography.intel.render.projects,
    "get",
    return_value=PROJECTS_RESPONSE,
)
@patch.object(
    cartography.intel.render.tenants,
    "get",
    return_value=OWNERS_RESPONSE,
)
def test_render_cleanup_removes_stale_projects(
    mock_get_owners,
    mock_get_projects,
    neo4j_session,
):
    # Arrange: one full sync, then everything upstream is gone.
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        render_api_key="test-api-key",
    )
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Act: re-sync with the project removed upstream, under a new update tag. The
    # tenant/workspace itself is still visible - only its project inventory changed.
    mock_get_projects.return_value = []
    config.update_tag = TEST_UPDATE_TAG_2
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert: the stale project is gone, but the tenant survives.
    assert check_nodes(neo4j_session, "RenderTenant", ["id"]) == {
        (TEST_OWNER_ID,),
    }
    assert check_nodes(neo4j_session, "RenderProject", ["id"]) == set()
