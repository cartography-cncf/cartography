from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.tables
import cartography.intel.databricks.vector_search
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.tables import DATABRICKS_TABLES
from tests.data.databricks.vector_search import DATABRICKS_VECTOR_SEARCH_ENDPOINTS
from tests.data.databricks.vector_search import DATABRICKS_VECTOR_SEARCH_INDEXES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
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
    cartography.intel.databricks.vector_search,
    "get_indexes",
    return_value=DATABRICKS_VECTOR_SEARCH_INDEXES,
)
@patch.object(
    cartography.intel.databricks.vector_search,
    "get_endpoints",
    return_value=DATABRICKS_VECTOR_SEARCH_ENDPOINTS,
)
def test_load_databricks_vector_search(mock_ep, mock_idx, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    cartography.intel.databricks.tables.load_tables(
        neo4j_session,
        cartography.intel.databricks.tables.transform(DATABRICKS_TABLES),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.databricks.vector_search.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksVectorSearchEndpoint",
        ["id", "name", "state"],
    ) == {(scoped("vs-endpoint-prod"), "vs-endpoint-prod", "ONLINE")}

    assert check_nodes(
        neo4j_session,
        "DatabricksVectorSearchIndex",
        ["id", "name", "index_type"],
    ) == {
        (
            scoped("prod.finance.customers_index"),
            "prod.finance.customers_index",
            "DELTA_SYNC",
        ),
    }

    # Index -> Endpoint USES_ENDPOINT
    assert check_rels(
        neo4j_session,
        "DatabricksVectorSearchIndex",
        "id",
        "DatabricksVectorSearchEndpoint",
        "id",
        "USES_ENDPOINT",
        rel_direction_right=True,
    ) == {(scoped("prod.finance.customers_index"), scoped("vs-endpoint-prod"))}

    # Index -> source Table SOURCED_FROM (matched by full_name)
    assert check_rels(
        neo4j_session,
        "DatabricksVectorSearchIndex",
        "id",
        "DatabricksTable",
        "full_name",
        "SOURCED_FROM",
        rel_direction_right=True,
    ) == {(scoped("prod.finance.customers_index"), "prod.finance.customers")}
