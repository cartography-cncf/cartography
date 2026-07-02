from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.clean_rooms
from tests.data.databricks.clean_rooms import DATABRICKS_CLEAN_ROOMS
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_CLEAN_ROOM_ID = f"{DATABRICKS_METASTORE_ID}/carto_test_clean_room"


@patch.object(
    cartography.intel.databricks.clean_rooms,
    "get",
    return_value=(DATABRICKS_CLEAN_ROOMS, True),
)
def test_load_databricks_clean_rooms(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    complete = cartography.intel.databricks.clean_rooms.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )
    assert complete is True

    assert check_nodes(
        neo4j_session,
        "DatabricksCleanRoom",
        ["id", "name", "access_restricted"],
    ) == {
        (_CLEAN_ROOM_ID, "carto_test_clean_room", "CSP_MISCONFIGURED"),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksCleanRoom",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(_CLEAN_ROOM_ID, DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksCleanRoom",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(DATABRICKS_METASTORE_ID, _CLEAN_ROOM_ID)}
