from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.functions
from tests.data.databricks.functions import DATABRICKS_FUNCTIONS
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_catalogs import (
    _ensure_local_neo4j_has_test_catalogs,
)
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


@patch.object(
    cartography.intel.databricks.functions,
    "get",
    return_value=DATABRICKS_FUNCTIONS,
)
def test_load_databricks_functions(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    cartography.intel.databricks.functions.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        [],
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksFunction",
        ["id", "name", "security_type"],
    ) == {(_uc_id("prod.finance.mask_ssn"), "mask_ssn", "DEFINER")}

    # Schema -> Function CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksSchema",
        "id",
        "DatabricksFunction",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(_uc_id("prod.finance"), _uc_id("prod.finance.mask_ssn"))}
