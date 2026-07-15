from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.service_principals
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
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
    cartography.intel.databricks.service_principals,
    "get",
    return_value=DATABRICKS_SERVICE_PRINCIPALS,
)
def test_load_databricks_service_principals(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_groups(neo4j_session)

    cartography.intel.databricks.service_principals.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    expected_nodes = {
        (
            scoped("12345678901234"),
            "12345678901234",
            "abcd1234-5678-90ab-cdef-1234567890ab",
            "cartography-sp",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DatabricksServicePrincipal",
            ["id", "scim_id", "application_id", "display_name"],
        )
        == expected_nodes
    )

    # ServiceAccount ontology label is applied
    assert check_nodes(neo4j_session, "ServiceAccount", ["id"]) >= {
        (scoped("12345678901234"),),
    }

    # SP -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(scoped("12345678901234"), DATABRICKS_WORKSPACE_ID)}

    # SP -> Group MEMBER_OF
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "id",
        "DatabricksGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {(scoped("12345678901234"), scoped("80972003232721"))}
