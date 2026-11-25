from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.pylon
from cartography.config import Config


@patch.object(cartography.intel.pylon.organization, "sync")
def test_start_pylon_ingestion_skips_without_token(mock_sync):
    # Arrange
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=1)

    # Act
    cartography.intel.pylon.start_pylon_ingestion(MagicMock(), config)

    # Assert
    mock_sync.assert_not_called()
