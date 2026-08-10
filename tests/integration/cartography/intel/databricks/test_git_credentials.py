from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.git_credentials
from tests.data.databricks.git_credentials import DATABRICKS_GIT_CREDENTIALS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_CREDENTIAL_ID = "6273842934"


@patch.object(
    cartography.intel.databricks.git_credentials,
    "get",
    return_value=DATABRICKS_GIT_CREDENTIALS,
)
def test_load_databricks_git_credentials(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.git_credentials.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksGitCredential",
        ["id", "git_provider", "git_username"],
    ) == {(scoped(_CREDENTIAL_ID), "gitHub", "carto-bot")}

    assert check_rels(
        neo4j_session,
        "DatabricksGitCredential",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_CREDENTIAL_ID), DATABRICKS_WORKSPACE_ID)}
