from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.users
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_groups import (
    _ensure_local_neo4j_has_test_groups,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.users,
    "get",
    return_value=DATABRICKS_USERS,
)
def test_load_databricks_users(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_groups(neo4j_session)

    # Act
    cartography.intel.databricks.users.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # Assert user nodes
    expected_nodes = {
        (
            scoped("70718330587535"),
            "70718330587535",
            "jeremy@subimage.io",
            "jeremy@subimage.io",
        ),
        (
            scoped("76890358753905"),
            "76890358753905",
            "kunaal@subimage.io",
            "kunaal@subimage.io",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DatabricksUser",
            ["id", "scim_id", "user_name", "email"],
        )
        == expected_nodes
    )

    # UserAccount ontology label is applied
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) >= {
        (scoped("70718330587535"),),
        (scoped("76890358753905"),),
    }

    # Assert User -> Workspace RESOURCE
    expected_rels = {
        (scoped("70718330587535"), DATABRICKS_WORKSPACE_ID),
        (scoped("76890358753905"), DATABRICKS_WORKSPACE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "DatabricksUser",
            "id",
            "DatabricksWorkspace",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert User -> Group MEMBER_OF
    expected_rels = {
        (scoped("70718330587535"), scoped("87707764220300")),
        (scoped("70718330587535"), scoped("80972003232721")),
        (scoped("76890358753905"), scoped("87707764220300")),
    }
    assert (
        check_rels(
            neo4j_session,
            "DatabricksUser",
            "id",
            "DatabricksGroup",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
