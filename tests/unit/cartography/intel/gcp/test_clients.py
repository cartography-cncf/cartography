from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.clients import build_artifact_registry_client


def test_build_artifact_registry_client_uses_resolved_credentials():
    credentials = MagicMock()

    with (
        patch(
            "cartography.intel.gcp.clients.get_gcp_credentials",
            return_value=credentials,
        ),
        patch(
            "cartography.intel.gcp.clients.ArtifactRegistryClient",
        ) as mock_client,
    ):
        build_artifact_registry_client()

    mock_client.assert_called_once_with(credentials=credentials)
