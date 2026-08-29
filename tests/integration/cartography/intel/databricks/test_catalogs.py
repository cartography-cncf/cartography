from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.catalogs
from tests.data.databricks.catalogs import DATABRICKS_CATALOGS
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


def _ensure_local_neo4j_has_test_catalogs(neo4j_session):
    cartography.intel.databricks.catalogs.load_catalogs(
        neo4j_session,
        cartography.intel.databricks.catalogs.transform(DATABRICKS_CATALOGS),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


def _catalog_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


@patch.object(
    cartography.intel.databricks.catalogs,
    "get",
    return_value=DATABRICKS_CATALOGS,
)
def test_load_databricks_catalogs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    cartography.intel.databricks.catalogs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksCatalog",
        ["id", "name", "catalog_type", "isolation_mode"],
    ) == {
        (_catalog_id("workspace"), "workspace", "MANAGED_CATALOG", "ISOLATED"),
        (_catalog_id("prod"), "prod", "MANAGED_CATALOG", "OPEN"),
    }

    # Catalog -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksCatalog",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (_catalog_id("workspace"), DATABRICKS_WORKSPACE_ID),
        (_catalog_id("prod"), DATABRICKS_WORKSPACE_ID),
    }

    # Metastore -> Catalog CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksCatalog",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (DATABRICKS_METASTORE_ID, _catalog_id("workspace")),
        (DATABRICKS_METASTORE_ID, _catalog_id("prod")),
    }
