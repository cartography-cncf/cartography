from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.clusters
import cartography.intel.databricks.jobs
from tests.data.databricks.clusters import DATABRICKS_CLUSTERS
from tests.data.databricks.jobs import DATABRICKS_JOBS
from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_pipelines import (
    _ensure_local_neo4j_has_test_pipelines,
)
from tests.integration.cartography.intel.databricks.test_pipelines import (
    _ensure_local_neo4j_has_test_principals,
)
from tests.integration.cartography.intel.databricks.test_sql_warehouses import (
    _ensure_local_neo4j_has_test_warehouses,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_JOB1 = "1011944831447606"
_JOB2 = "2022955942558717"
_PIPELINE_ID = "e66810c3-f9ba-4bbd-b9af-4e23bd2de755"


@patch.object(
    cartography.intel.databricks.jobs,
    "get",
    return_value=DATABRICKS_JOBS,
)
def test_load_databricks_jobs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_principals(neo4j_session)
    _ensure_local_neo4j_has_test_warehouses(neo4j_session)
    _ensure_local_neo4j_has_test_pipelines(neo4j_session)
    cartography.intel.databricks.clusters.load_clusters(
        neo4j_session,
        cartography.intel.databricks.clusters.transform(
            DATABRICKS_CLUSTERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.databricks.jobs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksJob",
        ["id", "name", "schedule_pause_status", "continuous"],
    ) == {
        (scoped(_JOB1), "carto-test-job", "PAUSED", False),
        (scoped(_JOB2), "carto-sp-job", None, True),
    }

    # Job -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksJob",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped(_JOB1), DATABRICKS_WORKSPACE_ID),
        (scoped(_JOB2), DATABRICKS_WORKSPACE_ID),
    }

    # Job -> User RUN_AS (job 1 runs as a user)
    assert check_rels(
        neo4j_session,
        "DatabricksJob",
        "id",
        "DatabricksUser",
        "id",
        "RUN_AS",
        rel_direction_right=True,
    ) == {(scoped(_JOB1), scoped("70718330587535"))}

    # Job -> ServicePrincipal RUN_AS (job 2 runs as a service principal)
    assert check_rels(
        neo4j_session,
        "DatabricksJob",
        "id",
        "DatabricksServicePrincipal",
        "id",
        "RUN_AS",
        rel_direction_right=True,
    ) == {(scoped(_JOB2), scoped("12345678901234"))}

    # Job -> Task HAS_TASK
    assert check_rels(
        neo4j_session,
        "DatabricksJob",
        "id",
        "DatabricksJobTask",
        "id",
        "HAS_TASK",
        rel_direction_right=True,
    ) == {
        (scoped(_JOB1), f"{scoped(_JOB1)}/carto_task_nb"),
        (scoped(_JOB1), f"{scoped(_JOB1)}/refresh_pipeline"),
        (scoped(_JOB2), f"{scoped(_JOB2)}/sp_task"),
    }

    # Task -> Pipeline RUNS_PIPELINE (only the pipeline_task)
    assert check_rels(
        neo4j_session,
        "DatabricksJobTask",
        "id",
        "DatabricksPipeline",
        "id",
        "RUNS_PIPELINE",
        rel_direction_right=True,
    ) == {(f"{scoped(_JOB1)}/refresh_pipeline", scoped(_PIPELINE_ID))}

    # Task -> Warehouse USES_WAREHOUSE (the sql_task)
    assert check_rels(
        neo4j_session,
        "DatabricksJobTask",
        "id",
        "DatabricksSqlWarehouse",
        "id",
        "USES_WAREHOUSE",
        rel_direction_right=True,
    ) == {(f"{scoped(_JOB1)}/refresh_pipeline", scoped(DATABRICKS_WAREHOUSE_ID))}

    # Task -> Cluster USES_CLUSTER (the task targeting an existing cluster)
    assert check_rels(
        neo4j_session,
        "DatabricksJobTask",
        "id",
        "DatabricksCluster",
        "id",
        "USES_CLUSTER",
        rel_direction_right=True,
    ) == {(f"{scoped(_JOB2)}/sp_task", scoped("0202-cluster-aaaa"))}
