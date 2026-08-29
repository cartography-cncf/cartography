from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.alerts
from tests.data.databricks.alerts import DATABRICKS_ALERTS
from tests.data.databricks.queries import DATABRICKS_QUERY_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_queries import (
    _ensure_local_neo4j_has_test_queries,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
_ALERT_ID = "b24eb01c-16d1-4235-9caa-428b62f969f2"


@patch.object(
    cartography.intel.databricks.alerts,
    "get",
    return_value=DATABRICKS_ALERTS,
)
def test_load_databricks_alerts(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_queries(neo4j_session)

    cartography.intel.databricks.alerts.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksAlert",
        ["id", "display_name", "condition_op", "owner_user_name"],
    ) == {
        (
            scoped(_ALERT_ID),
            "carto-test-alert",
            "GREATER_THAN",
            "jeremy@subimage.io",
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksAlert",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped(_ALERT_ID), DATABRICKS_WORKSPACE_ID)}

    assert check_rels(
        neo4j_session,
        "DatabricksAlert",
        "id",
        "DatabricksQuery",
        "id",
        "MONITORS",
        rel_direction_right=True,
    ) == {(scoped(_ALERT_ID), scoped(DATABRICKS_QUERY_ID))}
