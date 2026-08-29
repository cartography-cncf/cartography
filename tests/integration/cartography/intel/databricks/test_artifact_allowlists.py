from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.artifact_allowlists
from tests.data.databricks.artifact_allowlists import DATABRICKS_ARTIFACT_ALLOWLISTS
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


@patch.object(
    cartography.intel.databricks.artifact_allowlists,
    "get",
    return_value=(DATABRICKS_ARTIFACT_ALLOWLISTS, True),
)
def test_load_databricks_artifact_allowlists(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    cartography.intel.databricks.artifact_allowlists.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksArtifactAllowlist",
        ["id", "artifact_type"],
    ) == {
        (f"{DATABRICKS_METASTORE_ID}/INIT_SCRIPT", "INIT_SCRIPT"),
        (f"{DATABRICKS_METASTORE_ID}/LIBRARY_MAVEN", "LIBRARY_MAVEN"),
    }

    # Metastore -> ArtifactAllowlist CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksArtifactAllowlist",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (DATABRICKS_METASTORE_ID, f"{DATABRICKS_METASTORE_ID}/INIT_SCRIPT"),
        (DATABRICKS_METASTORE_ID, f"{DATABRICKS_METASTORE_ID}/LIBRARY_MAVEN"),
    }
