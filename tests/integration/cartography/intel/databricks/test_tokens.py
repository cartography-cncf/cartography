from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.service_principals
import cartography.intel.databricks.tokens
import cartography.intel.databricks.users
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.tokens import DATABRICKS_TOKENS
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_users_and_sps(neo4j_session):
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


@patch.object(
    cartography.intel.databricks.tokens,
    "get",
    return_value=DATABRICKS_TOKENS,
)
def test_load_databricks_tokens(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _seed_users_and_sps(neo4j_session)

    cartography.intel.databricks.tokens.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    expected_nodes = {
        (scoped("token-abc"), "token-abc", "ci/cd token", scoped("70718330587535")),
        (
            scoped("token-sp"),
            "token-sp",
            "service principal token",
            scoped("12345678901234"),
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "DatabricksToken",
            ["id", "token_id", "comment", "owner_id"],
        )
        == expected_nodes
    )

    # Token -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksToken",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("token-abc"), DATABRICKS_WORKSPACE_ID),
        (scoped("token-sp"), DATABRICKS_WORKSPACE_ID),
    }

    # User OWNER_OF Token (token-abc owned by Jeremy)
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "id",
        "DatabricksToken",
        "id",
        "OWNER_OF",
        rel_direction_right=True,
    ) == {(scoped("70718330587535"), scoped("token-abc"))}

    # ServicePrincipal OWNER_OF Token (token-sp owned by SP)
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "id",
        "DatabricksToken",
        "id",
        "OWNER_OF",
        rel_direction_right=True,
    ) == {(scoped("12345678901234"), scoped("token-sp"))}


def test_token_ids_are_workspace_scoped(neo4j_session):
    """Two workspaces with overlapping token_ids must stay as separate nodes."""
    workspace_a = "workspace-a.cloud.databricks.com"
    workspace_b = "workspace-b.cloud.databricks.com"
    shared_payload = [
        {
            "token_id": "shared-token",
            "comment": "shared",
            "creation_time": 1,
            "expiry_time": -1,
            "owner_id": 1,
            "created_by_id": 1,
            "created_by_username": "x",
        },
    ]

    cartography.intel.databricks.tokens.load_tokens(
        neo4j_session,
        cartography.intel.databricks.tokens.transform(shared_payload, workspace_a),
        workspace_a,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.tokens.load_tokens(
        neo4j_session,
        cartography.intel.databricks.tokens.transform(shared_payload, workspace_b),
        workspace_b,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksToken",
        ["id", "token_id"],
    ) >= {
        (f"{workspace_a}/shared-token", "shared-token"),
        (f"{workspace_b}/shared-token", "shared-token"),
    }
