from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.clean_rooms
from tests.data.databricks.clean_rooms import DATABRICKS_CLEAN_ROOMS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.clean_rooms,
    "get",
    return_value=DATABRICKS_CLEAN_ROOMS,
)
def test_load_databricks_clean_rooms(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.clean_rooms.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksCleanRoom",
        ["id", "name", "access_restricted"],
    ) == {
        (scoped("carto_test_clean_room"), "carto_test_clean_room", "CSP_MISCONFIGURED"),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksCleanRoom",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped("carto_test_clean_room"), DATABRICKS_WORKSPACE_ID)}
