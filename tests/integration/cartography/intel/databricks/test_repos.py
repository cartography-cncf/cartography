from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.repos
from tests.data.databricks.repos import DATABRICKS_REPOS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_REPO_ID = "1877866129247212"


@patch.object(
    cartography.intel.databricks.repos,
    "get",
    return_value=DATABRICKS_REPOS,
)
def test_load_databricks_repos(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.repos.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksRepo",
        ["id", "provider", "branch"],
    ) == {(scoped(_REPO_ID), "gitHub", "ide")}

    assert check_rels(
        neo4j_session,
        "DatabricksRepo",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_REPO_ID), DATABRICKS_WORKSPACE_ID)}
