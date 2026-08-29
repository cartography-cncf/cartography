from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.schemas
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.schemas import DATABRICKS_SCHEMAS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_catalogs import (
    _ensure_local_neo4j_has_test_catalogs,
)
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_schemas(neo4j_session):
    cartography.intel.databricks.schemas.load_schemas(
        neo4j_session,
        cartography.intel.databricks.schemas.transform(DATABRICKS_SCHEMAS),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


@patch.object(
    cartography.intel.databricks.schemas,
    "get",
    return_value=DATABRICKS_SCHEMAS,
)
def test_load_databricks_schemas(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)

    cartography.intel.databricks.schemas.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        [],
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksSchema",
        ["id", "name", "catalog_name"],
    ) == {
        (_uc_id("workspace.default"), "default", "workspace"),
        (_uc_id("prod.finance"), "finance", "prod"),
    }

    # Catalog -> Schema CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksCatalog",
        "id",
        "DatabricksSchema",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (_uc_id("workspace"), _uc_id("workspace.default")),
        (_uc_id("prod"), _uc_id("prod.finance")),
    }
