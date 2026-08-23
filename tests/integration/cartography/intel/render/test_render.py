from unittest.mock import patch

import cartography.intel.render
import cartography.intel.render.environments
import cartography.intel.render.projects
import cartography.intel.render.services
import cartography.intel.render.tenants
from cartography.config import Config
from tests.data.render.data import ENVIRONMENTS_RESPONSE
from tests.data.render.data import LATEST_DEPLOY_RESPONSE
from tests.data.render.data import OWNERS_RESPONSE
from tests.data.render.data import PROJECTS_RESPONSE
from tests.data.render.data import SERVICES_RESPONSE
from tests.data.render.data import TEST_OWNER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 223456789
TEST_PROJECT_ID = "prj-test001"
TEST_ENVIRONMENT_ID = "evn-test001"
TEST_SERVICE_ID = "srv-test001"


@patch.object(
    cartography.intel.render.services,
    "get_latest_deploy",
    return_value=LATEST_DEPLOY_RESPONSE,
)
@patch.object(
    cartography.intel.render.services,
    "get",
    return_value=SERVICES_RESPONSE,
)
@patch.object(
    cartography.intel.render.environments,
    "get",
    return_value=ENVIRONMENTS_RESPONSE,
)
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
def test_start_render_ingestion(
    mock_get_owners,
    mock_get_projects,
    mock_get_environments,
    mock_get_services,
    mock_get_latest_deploy,
    neo4j_session,
):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        render_api_key="test-api-key",
    )

    # Act
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert nodes
    assert check_nodes(neo4j_session, "RenderTenant", ["id", "name"]) == {
        (TEST_OWNER_ID, "cartography-test-workspace"),
    }
    assert check_nodes(neo4j_session, "RenderProject", ["id", "name"]) == {
        (TEST_PROJECT_ID, "cartography-test-project"),
    }
    assert check_nodes(
        neo4j_session,
        "RenderEnvironment",
        ["id", "name", "project_id"],
    ) == {
        (TEST_ENVIRONMENT_ID, "production", TEST_PROJECT_ID),
    }
    assert check_nodes(
        neo4j_session,
        "RenderService",
        ["id", "name", "environment_id"],
    ) == {
        (TEST_SERVICE_ID, "cartography-test-service", TEST_ENVIRONMENT_ID),
    }
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_name", "_ont_type", "_ont_state", "_ont_source"],
    ) == {
        # "live" (the raw deploy status) normalizes to the shared ComputeInstance
        # canonical state "running". _ont_type comes from the service's plan
        # ("starter"), not its runtime - consistent with every other provider's
        # ComputeInstance.type mapping (instance size/plan, not OS/runtime).
        (TEST_SERVICE_ID, "cartography-test-service", "starter", "running", "render"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {
        (TEST_OWNER_ID,),
    }

    # Assert relationships
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
    assert check_rels(
        neo4j_session,
        "RenderTenant",
        "id",
        "RenderEnvironment",
        "id",
        "RESOURCE",
    ) == {
        (TEST_OWNER_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderProject",
        "id",
        "RenderEnvironment",
        "id",
        "CONTAINS",
    ) == {
        (TEST_PROJECT_ID, TEST_ENVIRONMENT_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderTenant",
        "id",
        "RenderService",
        "id",
        "RESOURCE",
    ) == {
        (TEST_OWNER_ID, TEST_SERVICE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RenderEnvironment",
        "id",
        "RenderService",
        "id",
        "CONTAINS",
    ) == {
        (TEST_ENVIRONMENT_ID, TEST_SERVICE_ID),
    }


@patch.object(
    cartography.intel.render.services,
    "get_latest_deploy",
    return_value=LATEST_DEPLOY_RESPONSE,
)
@patch.object(
    cartography.intel.render.services,
    "get",
    return_value=SERVICES_RESPONSE,
)
@patch.object(
    cartography.intel.render.environments,
    "get",
    return_value=ENVIRONMENTS_RESPONSE,
)
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
def test_render_cleanup_removes_stale_resources(
    mock_get_owners,
    mock_get_projects,
    mock_get_environments,
    mock_get_services,
    mock_get_latest_deploy,
    neo4j_session,
):
    # Arrange: one full sync, then everything upstream is gone.
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        render_api_key="test-api-key",
    )
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Act: re-sync with everything but the tenant removed upstream, under a new
    # update tag. The tenant/workspace itself is still visible - only its resource
    # inventory changed.
    mock_get_projects.return_value = []
    mock_get_environments.return_value = []
    mock_get_services.return_value = []
    config.update_tag = TEST_UPDATE_TAG_2
    cartography.intel.render.start_render_ingestion(neo4j_session, config)

    # Assert: the stale resources are gone, but the tenant survives.
    assert check_nodes(neo4j_session, "RenderTenant", ["id"]) == {
        (TEST_OWNER_ID,),
    }
    assert check_nodes(neo4j_session, "RenderProject", ["id"]) == set()
    assert check_nodes(neo4j_session, "RenderEnvironment", ["id"]) == set()
    assert check_nodes(neo4j_session, "RenderService", ["id"]) == set()
