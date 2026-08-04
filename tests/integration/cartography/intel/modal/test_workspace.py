import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.modal.workspace
import tests.data.modal.workspace
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = tests.data.modal.workspace.MODAL_WORKSPACE["id"]


def _ensure_local_neo4j_has_test_workspace(neo4j_session):
    """Seed the tenant node. Imported by every other Modal test."""
    workspace = cartography.intel.modal.workspace.transform(
        tests.data.modal.workspace.MODAL_WORKSPACE,
    )
    cartography.intel.modal.workspace.load_workspace(
        neo4j_session,
        [workspace],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.modal.workspace,
    "get_workspace",
    return_value=tests.data.modal.workspace.MODAL_WORKSPACE,
)
def test_load_modal_workspace(mock_get, neo4j_session):
    # Arrange
    client = MagicMock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    asyncio.run(
        cartography.intel.modal.workspace.sync(
            neo4j_session,
            client,
            common_job_parameters,
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalWorkspace", ["id", "name", "slug"]) == {
        (TEST_WORKSPACE_ID, "example-workspace", "example-workspace"),
    }


@patch.object(
    cartography.intel.modal.workspace,
    "get_workspace",
    return_value=tests.data.modal.workspace.MODAL_WORKSPACE,
)
def test_modal_workspace_records_syncing_credential(mock_get, neo4j_session):
    """Modal has no read-only token scope, so which credential ran the sync is a
    security-relevant property and must land on the node."""
    # Arrange
    # Act
    asyncio.run(
        cartography.intel.modal.workspace.sync(
            neo4j_session,
            MagicMock(),
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ModalWorkspace",
        ["id", "synced_with_principal_type", "synced_with_token_name"],
    ) == {(TEST_WORKSPACE_ID, "user", "cartography")}


@patch.object(
    cartography.intel.modal.workspace,
    "get_workspace",
    return_value=tests.data.modal.workspace.MODAL_WORKSPACE,
)
def test_modal_workspace_carries_tenant_label(mock_get, neo4j_session):
    # Arrange
    # Act
    asyncio.run(
        cartography.intel.modal.workspace.sync(
            neo4j_session,
            MagicMock(),
            {"UPDATE_TAG": TEST_UPDATE_TAG},
        )
    )

    # Assert
    result = neo4j_session.run(
        "MATCH (w:ModalWorkspace {id: $id}) RETURN labels(w) AS labels",
        id=TEST_WORKSPACE_ID,
    )
    labels = set(result.single()["labels"])
    assert "Tenant" in labels
