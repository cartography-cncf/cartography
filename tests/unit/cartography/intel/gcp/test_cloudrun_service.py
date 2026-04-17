from unittest.mock import MagicMock
from unittest.mock import patch

from googleapiclient.errors import HttpError

from cartography.intel.gcp.cloudrun.service import get_services


def test_get_services_skips_permission_denied_locations():
    client = MagicMock()
    services_resource = (
        client.projects.return_value.locations.return_value.services.return_value
    )
    services_resource.list.side_effect = [MagicMock(), MagicMock()]
    services_resource.list_next.return_value = None

    forbidden_response = MagicMock()
    forbidden_response.status = 403

    with patch(
        "cartography.intel.gcp.cloudrun.service.gcp_api_execute_with_retry",
        side_effect=[
            HttpError(forbidden_response, b'{"error":{"message":"denied"}}'),
            {
                "services": [
                    {"name": "projects/test-project/locations/us-central1/services/api"}
                ]
            },
        ],
    ):
        services = get_services(
            client,
            "test-project",
            locations={
                "projects/test-project/locations/me-central2",
                "projects/test-project/locations/us-central1",
            },
        )

    assert services == [
        {"name": "projects/test-project/locations/us-central1/services/api"}
    ]
