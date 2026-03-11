from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied

from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations


def test_get_artifact_registry_locations_success():
    client = MagicMock()
    client.list_locations.return_value.locations = [
        MagicMock(location_id="us-central1"),
        MagicMock(location_id="europe-west1"),
    ]

    locations = get_artifact_registry_locations(client, "test-project")

    assert locations == ["us-central1", "europe-west1"]
    client.list_locations.assert_called_once_with(
        request={"name": "projects/test-project"}
    )


def test_get_artifact_registry_locations_permission_denied_returns_empty():
    client = MagicMock()
    client.list_locations.side_effect = PermissionDenied("Permission denied")

    locations = get_artifact_registry_locations(client, "test-project")

    assert locations == []


def test_get_artifact_registry_locations_billing_disabled_returns_empty():
    client = MagicMock()
    client.list_locations.side_effect = GoogleAPICallError(
        "This API method requires billing to be enabled. BILLING_DISABLED"
    )

    locations = get_artifact_registry_locations(client, "test-project")

    assert locations == []


def test_get_artifact_registry_locations_unknown_error_raises():
    client = MagicMock()
    client.list_locations.side_effect = GoogleAPICallError("backend failure")

    with pytest.raises(GoogleAPICallError):
        get_artifact_registry_locations(client, "test-project")
