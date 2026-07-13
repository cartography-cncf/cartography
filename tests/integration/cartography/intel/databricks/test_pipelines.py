from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.pipelines
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.users
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.pipelines import DATABRICKS_PIPELINES
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
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
_PIPELINE_ID = "e66810c3-f9ba-4bbd-b9af-4e23bd2de755"


def _ensure_local_neo4j_has_test_principals(neo4j_session):
    cartography.intel.databricks.users.load_users(
        neo4j_session,
        cartography.intel.databricks.users.transform(
            DATABRICKS_USERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.service_principals.load_service_principals(
        neo4j_session,
        cartography.intel.databricks.service_principals.transform(
            DATABRICKS_SERVICE_PRINCIPALS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_pipelines(neo4j_session):
    cartography.intel.databricks.pipelines.load_pipelines(
        neo4j_session,
        cartography.intel.databricks.pipelines.transform(
            DATABRICKS_PIPELINES, DATABRICKS_WORKSPACE_ID, DATABRICKS_METASTORE_ID, {}
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.pipelines,
    "get",
    return_value=DATABRICKS_PIPELINES,
)
def test_load_databricks_pipelines(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_principals(neo4j_session)

    cartography.intel.databricks.pipelines.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksPipeline",
        ["id", "name", "catalog", "target_schema", "serverless"],
    ) == {
        (
            scoped(_PIPELINE_ID),
            "carto-test-pipeline",
            "workspace",
            "carto_test_schema",
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksPipeline",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_PIPELINE_ID), DATABRICKS_WORKSPACE_ID)}

    # Pipeline -> Catalog PUBLISHES_TO (catalog id is metastore-scoped).
    assert check_rels(
        neo4j_session,
        "DatabricksPipeline",
        "id",
        "DatabricksCatalog",
        "id",
        "PUBLISHES_TO",
        rel_direction_right=True,
    ) == {(scoped(_PIPELINE_ID), f"{DATABRICKS_METASTORE_ID}/workspace")}

    # Pipeline -> User RUN_AS (resolved to the workspace-scoped principal id).
    assert check_rels(
        neo4j_session,
        "DatabricksPipeline",
        "id",
        "DatabricksUser",
        "id",
        "RUN_AS",
        rel_direction_right=True,
    ) == {(scoped(_PIPELINE_ID), scoped("70718330587535"))}
