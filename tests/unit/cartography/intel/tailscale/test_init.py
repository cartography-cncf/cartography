from unittest.mock import MagicMock

from cartography.intel.tailscale import start_tailscale_ingestion


def test_tailscale_skips_when_not_configured() -> None:
    mock_config = MagicMock()
    mock_config.tailscale_token = None
    mock_config.tailscale_org = None
    mock_config.tailscale_oauth_client_id = None
    mock_config.tailscale_oauth_client_secret = None

    start_tailscale_ingestion(MagicMock(), mock_config)
