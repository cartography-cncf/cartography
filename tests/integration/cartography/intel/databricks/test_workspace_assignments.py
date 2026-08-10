from unittest.mock import Mock

import cartography.intel.databricks.workspace_assignments
from tests.data.databricks.account import account_scoped
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_workspaces import (
    DATABRICKS_ACCOUNT_WORKSPACE_NODE_IDS,
)
from tests.data.databricks.workspace_assignments import DATABRICKS_WORKSPACE_ASSIGNMENTS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_account_groups import (
    _ensure_local_neo4j_has_test_account_groups,
)
from tests.integration.cartography.intel.databricks.test_account_service_principals import (
    _ensure_local_neo4j_has_test_account_service_principals,
)
from tests.integration.cartography.intel.databricks.test_account_users import (
    _ensure_local_neo4j_has_test_account_users,
)
from tests.integration.cartography.intel.databricks.test_account_workspaces import (
    _ensure_local_neo4j_has_test_account_workspaces,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _api_get(uri, params=None):
    # The account permissionassignments URI ends with the numeric workspace id
    # followed by /permissionassignments; return the matching fixture payload.
    for numeric_id, payload in DATABRICKS_WORKSPACE_ASSIGNMENTS.items():
        if f"/workspaces/{numeric_id}/permissionassignments" in uri:
            return payload
    return {"permission_assignments": []}


def test_load_databricks_workspace_assignments(neo4j_session):
    # Arrange
    api_session = Mock()
    api_session.account_uri.side_effect = lambda suffix: (
        f"/api/2.0/accounts/{DATABRICKS_ACCOUNT_ID}{suffix}"
    )
    api_session.get.side_effect = _api_get
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_account_groups(neo4j_session)
    _ensure_local_neo4j_has_test_account_users(neo4j_session)
    _ensure_local_neo4j_has_test_account_service_principals(neo4j_session)
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)

    # Act
    cartography.intel.databricks.workspace_assignments.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        DATABRICKS_ACCOUNT_WORKSPACE_NODE_IDS,
        common_job_parameters,
    )

    prod = "dbc-aaeaddda-e52f.cloud.databricks.com"
    staging = "dbc-bbfbeeeb-f63a.cloud.databricks.com"

    # User -> Workspace ASSIGNED_TO
    assert check_rels(
        neo4j_session,
        "DatabricksAccountUser",
        "id",
        "DatabricksWorkspace",
        "id",
        "ASSIGNED_TO",
        rel_direction_right=True,
    ) == {(account_scoped("410001"), prod)}

    # Group -> Workspace ASSIGNED_TO
    assert check_rels(
        neo4j_session,
        "DatabricksAccountGroup",
        "id",
        "DatabricksWorkspace",
        "id",
        "ASSIGNED_TO",
        rel_direction_right=True,
    ) == {(account_scoped("310002"), prod)}

    # ServicePrincipal -> Workspace ASSIGNED_TO
    assert check_rels(
        neo4j_session,
        "DatabricksAccountServicePrincipal",
        "id",
        "DatabricksWorkspace",
        "id",
        "ASSIGNED_TO",
        rel_direction_right=True,
    ) == {(account_scoped("510001"), staging)}
