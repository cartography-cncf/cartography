from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.metastores
from tests.data.databricks.metastore import DATABRICKS_METASTORE
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_metastore(neo4j_session):
    cartography.intel.databricks.metastores.load_metastores(
        neo4j_session,
        cartography.intel.databricks.metastores.transform(DATABRICKS_METASTORE),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.metastores,
    "get",
    return_value=DATABRICKS_METASTORE,
)
def test_load_databricks_metastore(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    metastore_id = cartography.intel.databricks.metastores.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert metastore_id == DATABRICKS_METASTORE_ID

    assert check_nodes(
        neo4j_session,
        "DatabricksMetastore",
        ["id", "name", "cloud", "region"],
    ) == {
        (
            DATABRICKS_METASTORE_ID,
            "metastore_aws_us_west_2",
            "aws",
            "us-west-2",
        ),
    }

    # Workspace -> Metastore ASSIGNED_METASTORE
    assert check_rels(
        neo4j_session,
        "DatabricksWorkspace",
        "id",
        "DatabricksMetastore",
        "id",
        "ASSIGNED_METASTORE",
        rel_direction_right=True,
    ) == {(DATABRICKS_WORKSPACE_ID, DATABRICKS_METASTORE_ID)}
