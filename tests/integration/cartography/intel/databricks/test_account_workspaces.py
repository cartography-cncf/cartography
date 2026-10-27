from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks
import cartography.intel.databricks.account_workspaces
import cartography.intel.databricks.workspaces
from cartography.client.core.tx import load
from cartography.models.databricks.account import DatabricksAccountSchema
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
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    # Assert
    assert check_nodes(
        neo4j_session,
        "DatabricksWorkspace",
        ["id", "tokens_enabled", "max_token_lifetime_days", "workspace_name"],
    ) == {
        ("1234567890123456", True, 730, "prod"),
        ("6543210987654321", None, None, "staging"),
    }


def test_account_cleanup_keeps_other_accounts_workspace_edges(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    other_account_id = "00000000-0000-0000-0000-0000000000aa"
    load(
        neo4j_session,
        DatabricksAccountSchema(),
        [DATABRICKS_ACCOUNT, {**DATABRICKS_ACCOUNT, "id": other_account_id}],
        lastupdated=1,
    )
    prod, staging = cartography.intel.databricks.account_workspaces.transform(
        DATABRICKS_ACCOUNT_WORKSPACES
    )
    load_account_workspaces = (
        cartography.intel.databricks.account_workspaces.load_workspaces
    )
    load_account_workspaces(neo4j_session, [prod], DATABRICKS_ACCOUNT_ID, 1)
    load_account_workspaces(neo4j_session, [staging], other_account_id, 1)
    # Only the first account syncs under the new tag; the other one's run failed.
    load_account_workspaces(neo4j_session, [prod], DATABRICKS_ACCOUNT_ID, 2)

    # Act
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session,
        2,
        [
            cartography.intel.databricks.DatabricksSyncResult(
                workspace_id="1234567890123456", account_id=DATABRICKS_ACCOUNT_ID
            )
        ],
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "DatabricksAccount",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
    ) == {
        (DATABRICKS_ACCOUNT_ID, "1234567890123456"),
        (other_account_id, "6543210987654321"),
    }


def test_workspace_and_account_paths_share_one_node_for_a_vanity_host(
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_account(neo4j_session)
    api_session = Mock(host="https://analytics.example.com")
    api_session.get_with_headers.return_value = (
        {},
        {"x-databricks-org-id": "1234567890123456"},
    )

    # Act
    cartography.intel.databricks.workspaces.sync(
        neo4j_session, api_session, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )
    _ensure_local_neo4j_has_test_account_workspaces(neo4j_session)

    # Assert
    assert check_nodes(
        neo4j_session, "DatabricksWorkspace", ["id", "host", "deployment_name"]
    ) == {
        ("1234567890123456", "https://analytics.example.com", "dbc-aaeaddda-e52f"),
        ("6543210987654321", None, "dbc-bbfbeeeb-f63a"),
    }


def _seed_host_keyed_workspace(neo4j_session, legacy_id: str) -> None:
    """Recreate what earlier versions left: a host-keyed workspace with a cluster."""
    neo4j_session.run(
        "CREATE (:DatabricksWorkspace {id: $legacy, lastupdated: 1})"
        "-[:RESOURCE {lastupdated: 1}]->"
        "(:DatabricksCluster {id: $legacy + '/cluster', lastupdated: 1})",
        legacy=legacy_id,
    )


# DEPRECATED: covers the host-keyed workspace migration, removed in v1.0.0.
def test_workspace_cleanup_removes_its_host_keyed_node(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_host_keyed_workspace(neo4j_session, DATABRICKS_WORKSPACE["legacy_id"])
    cartography.intel.databricks.workspaces.load_workspaces(
        neo4j_session, [DATABRICKS_WORKSPACE], 2
    )

    # Act
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session,
        2,
        [
            cartography.intel.databricks.DatabricksSyncResult(
                workspace_id=DATABRICKS_WORKSPACE_ID
            )
        ],
    )

    # Assert
    assert check_nodes(neo4j_session, "DatabricksWorkspace", ["id"]) == {
        (DATABRICKS_WORKSPACE_ID,),
    }
    assert check_nodes(neo4j_session, "DatabricksCluster", ["id"]) == set()


# DEPRECATED: covers the host-keyed workspace migration, removed in v1.0.0.
def test_account_cleanup_removes_host_keyed_nodes_it_no_longer_lists(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_account(neo4j_session)
    legacy_id = "dbc-bbfbeeeb-f63a.cloud.databricks.com"
    _seed_host_keyed_workspace(neo4j_session, legacy_id)
    neo4j_session.run(
        "MATCH (a:DatabricksAccount {id: $account}), "
        "(w:DatabricksWorkspace {id: $legacy}) "
        "CREATE (a)-[:RESOURCE {lastupdated: 1}]->(w)",
        account=DATABRICKS_ACCOUNT_ID,
        legacy=legacy_id,
    )
    cartography.intel.databricks.account_workspaces.load_workspaces(
        neo4j_session,
        cartography.intel.databricks.account_workspaces.transform(
            DATABRICKS_ACCOUNT_WORKSPACES
        ),
        DATABRICKS_ACCOUNT_ID,
        2,
    )

    # Act
    cartography.intel.databricks.cleanup_databricks(
        neo4j_session,
        2,
        [
            cartography.intel.databricks.DatabricksSyncResult(
                workspace_id=DATABRICKS_WORKSPACE_ID,
                account_id=DATABRICKS_ACCOUNT_ID,
            )
        ],
    )

    # Assert
    assert check_nodes(neo4j_session, "DatabricksWorkspace", ["id"]) == {
        ("1234567890123456",),
        ("6543210987654321",),
    }
    assert check_nodes(neo4j_session, "DatabricksCluster", ["id"]) == set()
