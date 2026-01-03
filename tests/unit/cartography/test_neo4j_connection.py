from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.config import Config
from cartography.sync import run_with_config


@patch("cartography.sync.GraphDatabase.driver")
def test_neo4j_driver_init_with_idle_time(mock_driver):
    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        neo4j_max_connection_idle_time=120,
    )
    mock_sync = MagicMock()

    # Act
    run_with_config(mock_sync, config)

    # Assert
    mock_driver.assert_called_once()
    args, kwargs = mock_driver.call_args
    assert "max_connection_lifetime" in kwargs
    assert kwargs["max_connection_lifetime"] == 120
