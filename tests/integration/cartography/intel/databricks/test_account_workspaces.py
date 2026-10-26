from unittest.mock import Mock
from unittest.mock import patch

import pytest

import cartography.intel.databricks
import cartography.intel.databricks.account_workspaces
import cartography.intel.databricks.workspaces
from tests.data.databricks.account import DATABRICKS_ACCOUNT
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_workspaces import DATABRICKS_ACCOUNT_WORKSPACE_IDS
from tests.data.databricks.account_workspaces import DATABRICKS_ACCOUNT_WORKSPACES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account_workspaces(neo4j_session):
    cartography.intel.databricks.account_workspaces.load_workspaces(
        neo4j_session,
        cartography.intel.databricks.account_workspaces.transform(
            DATABRICKS_ACCOUNT_WORKSPACES
        ),
        DATABRICKS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.account_workspaces,
    "get",
    return_value=DATABRICKS_ACCOUNT_WORKSPACES,
)
def test_load_databricks_account_workspaces(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    api_session.host = "https://accounts.cloud.databricks.com"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    workspace_ids = cartography.intel.databricks.account_workspaces.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert workspace_ids == DATABRICKS_ACCOUNT_WORKSPACE_IDS

    # Assert workspace nodes carry the account-API numeric id + name
    assert check_nodes(
        neo4j_session,
        "DatabricksWorkspace",
        ["id", "workspace_id", "workspace_name", "deployment_name"],
    ) == {
        (
            "1234567890123456",
            "1234567890123456",
            "prod",
            "dbc-aaeaddda-e52f",
        ),
        (
            "6543210987654321",
            "6543210987654321",
            "staging",
            "dbc-bbfbeeeb-f63a",
        ),
    }

    # Assert Account -> Workspace RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccount",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (DATABRICKS_ACCOUNT_ID, "1234567890123456"),
        (DATABRICKS_ACCOUNT_ID, "6543210987654321"),
    }


def test_workspace_and_account_paths_keep_each_others_properties(neo4j_session):
    _ensure_local_neo4j_has_test_account(neo4j_session)

    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    assert check_nodes(
        neo4j_session,
        "DatabricksWorkspace",
        ["id", "tokens_enabled", "max_token_lifetime_days", "workspace_id"],
    ) == {
        (
            DATABRICKS_WORKSPACE_ID,
            DATABRICKS_WORKSPACE["tokens_enabled"],
            DATABRICKS_WORKSPACE["max_token_lifetime_days"],
            "1234567890123456",
        ),
        ("6543210987654321", None, None, "6543210987654321"),
    }


def test_account_cleanup_keeps_other_accounts_workspace_edges(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    other_account_id = "00000000-0000-0000-0000-0000000000aa"
    cartography.intel.databricks.account.load(
        neo4j_session,
        cartography.intel.databricks.account.DatabricksAccountSchema(),
        [DATABRICKS_ACCOUNT, {**DATABRICKS_ACCOUNT, "id": other_account_id}],
        lastupdated=1,
    )
    prod, staging = cartography.intel.databricks.account_workspaces.transform(
        DATABRICKS_ACCOUNT_WORKSPACES
    )
    load = cartography.intel.databricks.account_workspaces.load_workspaces
    load(neo4j_session, [prod], DATABRICKS_ACCOUNT_ID, 1)
    load(neo4j_session, [staging], other_account_id, 1)

    # Only the first account syncs under the new tag; the other one's run failed.
    load(neo4j_session, [prod], DATABRICKS_ACCOUNT_ID, 2)
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session,
        2,
        [
            cartography.intel.databricks.DatabricksSyncResult(
                prod["id"], DATABRICKS_ACCOUNT_ID
            )
        ],
    )

    assert check_rels(
        neo4j_session,
        "DatabricksAccount",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
    ) == {(DATABRICKS_ACCOUNT_ID, prod["id"]), (other_account_id, staging["id"])}


def test_workspace_and_account_paths_share_one_node_for_a_vanity_host(
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_account(neo4j_session)
    api_session = Mock(host="https://analytics.example.com")
    api_session.get_with_headers.return_value = (
        {},
        {"x-databricks-org-id": "1234567890123456"},
    )

    cartography.intel.databricks.workspaces.sync(
        neo4j_session, api_session, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)

    assert check_nodes(
        neo4j_session, "DatabricksWorkspace", ["id", "host", "deployment_name"]
    ) == {
        ("1234567890123456", "https://analytics.example.com", "dbc-aaeaddda-e52f"),
        ("6543210987654321", None, "dbc-bbfbeeeb-f63a"),
    }


# DEPRECATED: covers the host-keyed workspace migration, removed in v1.0.0.
@pytest.mark.parametrize(
    "account_id, legacy_id",
    [
        # Workspace-only: the workspace path links its old host-keyed node.
        (None, DATABRICKS_WORKSPACE["legacy_id"]),
        # Account mode: a workspace only the account path ever loaded.
        (DATABRICKS_ACCOUNT_ID, "dbc-bbfbeeeb-f63a.cloud.databricks.com"),
    ],
)
def test_cleanup_removes_host_keyed_workspace_and_its_resources(
    neo4j_session, account_id, legacy_id
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_account(neo4j_session)
    # What earlier versions left: a workspace keyed on its host, linked to the
    # account when one was configured, owning a cluster.
    neo4j_session.run(
        "CREATE (w:DatabricksWorkspace {id: $legacy, lastupdated: 1})"
        "-[:RESOURCE {lastupdated: 1}]->"
        "(:DatabricksCluster {id: $legacy + '/cluster', lastupdated: 1}) "
        "WITH w MATCH (a:DatabricksAccount {id: $account}) "
        "CREATE (a)-[:RESOURCE {lastupdated: 1}]->(w)",
        legacy=legacy_id,
        account=account_id,
    )

    cartography.intel.databricks.workspaces.load_workspaces(
        neo4j_session, [DATABRICKS_WORKSPACE], 2, account_id
    )
    if account_id is not None:
        cartography.intel.databricks.account_workspaces.load_workspaces(
            neo4j_session,
            cartography.intel.databricks.account_workspaces.transform(
                DATABRICKS_ACCOUNT_WORKSPACES
            ),
            account_id,
            2,
        )
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session,
        2,
        [
            cartography.intel.databricks.DatabricksSyncResult(
                DATABRICKS_WORKSPACE_ID, account_id
            )
        ],
    )

    workspace_ids = check_nodes(neo4j_session, "DatabricksWorkspace", ["id"])
    assert (legacy_id,) not in workspace_ids
    assert (DATABRICKS_WORKSPACE_ID,) in workspace_ids
    assert check_nodes(neo4j_session, "DatabricksCluster", ["id"]) == set()
