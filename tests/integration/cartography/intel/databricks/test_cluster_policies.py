from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.cluster_policies
from tests.data.databricks.cluster_policies import DATABRICKS_CLUSTER_POLICIES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.cluster_policies,
    "get",
    return_value=DATABRICKS_CLUSTER_POLICIES,
)
def test_load_databricks_cluster_policies(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.cluster_policies.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    expected_nodes = {
        (
            scoped("0001-policy-aaaa"),
            "0001-policy-aaaa",
            "Job Compute - Restricted",
            "jeremy@subimage.io",
        ),
        (
            scoped("0002-policy-bbbb"),
            "0002-policy-bbbb",
            "Personal Compute",
            None,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DatabricksClusterPolicy",
            ["id", "policy_id", "name", "creator_user_name"],
        )
        == expected_nodes
    )

    assert check_rels(
        neo4j_session,
        "DatabricksClusterPolicy",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("0001-policy-aaaa"), DATABRICKS_WORKSPACE_ID),
        (scoped("0002-policy-bbbb"), DATABRICKS_WORKSPACE_ID),
    }
