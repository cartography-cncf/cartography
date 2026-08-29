from unittest.mock import patch

import cartography.intel.databricks.jobs
import cartography.intel.databricks.notebooks
from tests.data.databricks.jobs import DATABRICKS_JOBS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_JOB1 = "1011944831447606"
_JOB2 = "2022955942558717"
_NB1 = "/Users/jeremy@subimage.io/carto_test_nb"
_NB2 = "/Shared/sp_nb"


def _seed_job_tasks(neo4j_session):
    cartography.intel.databricks.jobs.load_tasks(
        neo4j_session,
        cartography.intel.databricks.jobs.transform_tasks(
            DATABRICKS_JOBS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.notebooks,
    "get_referenced_notebook_paths",
    wraps=cartography.intel.databricks.notebooks.get_referenced_notebook_paths,
)
def test_load_databricks_notebooks(mock_get, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _seed_job_tasks(neo4j_session)

    cartography.intel.databricks.notebooks.sync(
        neo4j_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # One node per distinct notebook path referenced by a task; no other
    # workspace content is walked.
    assert check_nodes(neo4j_session, "DatabricksNotebook", ["id", "path"]) == {
        (scoped(_NB1), _NB1),
        (scoped(_NB2), _NB2),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksNotebook",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped(_NB1), DATABRICKS_WORKSPACE_ID),
        (scoped(_NB2), DATABRICKS_WORKSPACE_ID),
    }

    # Each notebook task links to the notebook it runs.
    assert check_rels(
        neo4j_session,
        "DatabricksJobTask",
        "id",
        "DatabricksNotebook",
        "id",
        "RUNS_NOTEBOOK",
        rel_direction_right=True,
    ) == {
        (f"{scoped(_JOB1)}/carto_task_nb", scoped(_NB1)),
        (f"{scoped(_JOB2)}/sp_task", scoped(_NB2)),
    }
