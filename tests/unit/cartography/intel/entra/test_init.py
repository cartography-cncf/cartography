from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from pytest import raises

import cartography.config
import cartography.intel.entra

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.entra,
    "RESOURCE_FUNCTIONS",
    [
        ("users", AsyncMock(side_effect=KeyError("users"))),
        ("groups", AsyncMock(side_effect=KeyError("groups"))),
        ("ous", AsyncMock(side_effect=KeyError("ous"))),
        ("applications", AsyncMock(side_effect=KeyError("applications"))),
    ],
)
def test_start_entra_ingestion_aggregates_exceptions_with_best_effort():
    # Arrange
    neo4j_session = MagicMock()
    config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        entra_best_effort_mode=True,
        entra_tenant_id="tenant",
        entra_client_id="client",
        entra_client_secret="secret",
    )

    # Act
    with raises(Exception) as e:
        cartography.intel.entra.start_entra_ingestion(neo4j_session, config)

    # Assert that we've collected 4 key errors along the way with best effort mode on.
    message = str(e.value)
    assert message.count("KeyError") == 4


def test_start_entra_ingestion_raises_first_exception_without_best_effort():
    # Arrange
    neo4j_session = MagicMock()
    config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        entra_best_effort_mode=False,
        entra_tenant_id="tenant",
        entra_client_id="client",
        entra_client_secret="secret",
    )

    # Create mock objects that we can reference later
    mock_users = AsyncMock(side_effect=KeyError("users"))
    mock_groups = AsyncMock()
    mock_ous = AsyncMock()
    mock_applications = AsyncMock()

    test_resource_functions = [
        ("users", mock_users),
        ("groups", mock_groups),
        ("ous", mock_ous),
        ("applications", mock_applications),
    ]

    # Act
    with patch.object(
        cartography.intel.entra,
        "RESOURCE_FUNCTIONS",
        test_resource_functions,
    ):
        with raises(Exception) as e:
            cartography.intel.entra.start_entra_ingestion(neo4j_session, config)

        assert isinstance(e.value, KeyError)
        # Assert that the first function was called exactly once and the rest were not called because
        # best effort mode is off.
        assert mock_users.call_count == 1
        assert mock_groups.call_count == 0
        assert mock_ous.call_count == 0
        assert mock_applications.call_count == 0
        assert str(e.value) == "'users'"


def test_start_entra_ingestion_runs_all_syncs():
    # Arrange
    neo4j_session = MagicMock()
    config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        entra_best_effort_mode=False,
        entra_tenant_id="tenant",
        entra_client_id="client",
        entra_client_secret="secret",
    )

    # Create mock objects that we can reference later
    mock_users = AsyncMock()
    mock_groups = AsyncMock()
    mock_ous = AsyncMock()
    mock_applications = AsyncMock()

    test_resource_functions = [
        ("users", mock_users),
        ("groups", mock_groups),
        ("ous", mock_ous),
        ("applications", mock_applications),
    ]

    # Act
    with patch.object(
        cartography.intel.entra,
        "RESOURCE_FUNCTIONS",
        test_resource_functions,
    ):
        cartography.intel.entra.start_entra_ingestion(neo4j_session, config)

        # Assert that all functions were called.
        assert mock_users.call_count == 1
        assert mock_groups.call_count == 1
        assert mock_ous.call_count == 1
        assert mock_applications.call_count == 1
