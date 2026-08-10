from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.groups
from tests.data.databricks.groups import DATABRICKS_GROUPS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_groups(neo4j_session):
    transformed = cartography.intel.databricks.groups.transform(
        DATABRICKS_GROUPS, DATABRICKS_WORKSPACE_ID
    )
    cartography.intel.databricks.groups.load_groups(
        neo4j_session,
        transformed,
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.groups,
    "get",
    return_value=DATABRICKS_GROUPS,
)
def test_load_databricks_groups(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.groups.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    expected_nodes = {
        (scoped("87707764220300"), "87707764220300", "account users"),
        (scoped("80972003232721"), "80972003232721", "admins"),
        (scoped("99999999999999"), "99999999999999", "nested-group"),
    }
    assert (
        check_nodes(neo4j_session, "DatabricksGroup", ["id", "scim_id", "display_name"])
        == expected_nodes
    )

    # UserGroup ontology label is applied
    assert check_nodes(neo4j_session, "UserGroup", ["id"]) >= {
        (scoped("87707764220300"),),
        (scoped("80972003232721"),),
        (scoped("99999999999999"),),
    }

    # Group -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("87707764220300"), DATABRICKS_WORKSPACE_ID),
        (scoped("80972003232721"), DATABRICKS_WORKSPACE_ID),
        (scoped("99999999999999"), DATABRICKS_WORKSPACE_ID),
    }

    # Nested group MEMBER_OF parent (nested-group is a member of admins)
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "id",
        "DatabricksGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {(scoped("99999999999999"), scoped("80972003232721"))}
