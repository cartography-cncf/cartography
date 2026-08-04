import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.modal.environments
import tests.data.modal.environments
from tests.integration.cartography.intel.modal.test_workspace import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _ensure_local_neo4j_has_test_environments(neo4j_session):
    """Seed the environment nodes. Imported by every environment-scoped Modal test."""
    environments = cartography.intel.modal.environments.transform(
        tests.data.modal.environments.MODAL_ENVIRONMENTS,
    )
    cartography.intel.modal.environments.load_environments(
        neo4j_session,
        environments,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.modal.environments,
    "list_environments",
    return_value=tests.data.modal.environments.MODAL_ENVIRONMENTS,
)
def test_load_modal_environments(mock_list, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
    }

    # Act
    asyncio.run(
        cartography.intel.modal.environments.sync(
            neo4j_session,
            MagicMock(),
            common_job_parameters,
        )
    )

    # Assert
    assert check_nodes(
        neo4j_session, "ModalEnvironment", ["id", "name", "is_default"]
    ) == {
        ("en-C3umado26sLFrhYfZjoWjL", "main", True),
        ("en-9ZKpQr4tVbNmXsLdEfGhJk", "prod", False),
    }
    assert check_rels(
        neo4j_session,
        "ModalEnvironment",
        "id",
        "ModalWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("en-C3umado26sLFrhYfZjoWjL", TEST_WORKSPACE_ID),
        ("en-9ZKpQr4tVbNmXsLdEfGhJk", TEST_WORKSPACE_ID),
    }


@patch.object(
    cartography.intel.modal.environments,
    "list_environments",
    return_value=tests.data.modal.environments.MODAL_ENVIRONMENTS,
)
def test_modal_environment_quota_fields(mock_list, neo4j_session):
    """Concurrency limits and the spend-limit flag are availability signals, so they must
    survive the transform. The cost figures on the same API message are deliberately not
    ingested."""
    # Arrange
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    # Act
    asyncio.run(
        cartography.intel.modal.environments.sync(
            neo4j_session,
            MagicMock(),
            {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
        )
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ModalEnvironment",
        ["name", "max_concurrent_gpus", "spend_limit_reached"],
    ) == {
        ("main", 0, False),
        ("prod", 8, True),
    }


@patch.object(cartography.intel.modal.environments, "list_environments")
def test_modal_environment_cleanup_removes_deleted(mock_list, neo4j_session):
    # Arrange: first sync sees both environments
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    mock_list.return_value = tests.data.modal.environments.MODAL_ENVIRONMENTS
    asyncio.run(
        cartography.intel.modal.environments.sync(
            neo4j_session,
            MagicMock(),
            {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
        )
    )

    # Act: the second sync no longer sees 'prod'
    mock_list.return_value = [tests.data.modal.environments.MODAL_ENVIRONMENTS[0]]
    asyncio.run(
        cartography.intel.modal.environments.sync(
            neo4j_session,
            MagicMock(),
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "WORKSPACE_ID": TEST_WORKSPACE_ID},
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalEnvironment", ["id"]) == {
        ("en-C3umado26sLFrhYfZjoWjL",),
    }
