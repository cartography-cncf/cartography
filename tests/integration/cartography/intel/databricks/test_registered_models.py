from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.registered_models
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.registered_models import DATABRICKS_MODEL_VERSIONS
from tests.data.databricks.registered_models import DATABRICKS_REGISTERED_MODELS
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
    cartography.intel.databricks.registered_models,
    "get_versions",
    return_value=DATABRICKS_MODEL_VERSIONS,
)
@patch.object(
    cartography.intel.databricks.registered_models,
    "get",
    return_value=DATABRICKS_REGISTERED_MODELS,
)
def test_load_databricks_registered_models(mock_get, mock_versions, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    cartography.intel.databricks.registered_models.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        [],
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksRegisteredModel",
        ["id", "name"],
    ) == {(_uc_id("prod.finance.churn_model"), "churn_model")}

    assert check_nodes(
        neo4j_session,
        "DatabricksModelVersion",
        ["id", "version", "status"],
    ) == {(f"{_uc_id('prod.finance.churn_model')}/1", 1, "READY")}

    # Schema -> RegisteredModel CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksSchema",
        "id",
        "DatabricksRegisteredModel",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(_uc_id("prod.finance"), _uc_id("prod.finance.churn_model"))}

    # RegisteredModel -> ModelVersion HAS_VERSION
    assert check_rels(
        neo4j_session,
        "DatabricksRegisteredModel",
        "id",
        "DatabricksModelVersion",
        "id",
        "HAS_VERSION",
        rel_direction_right=True,
    ) == {
        (
            _uc_id("prod.finance.churn_model"),
            f"{_uc_id('prod.finance.churn_model')}/1",
        )
    }
