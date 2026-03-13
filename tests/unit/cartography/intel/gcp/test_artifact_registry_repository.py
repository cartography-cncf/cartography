from unittest.mock import MagicMock

from cartography.intel.gcp.artifact_registry.repository import (
    get_artifact_registry_repositories,
)
from cartography.intel.gcp.util import GCP_API_NUM_RETRIES


def test_get_artifact_registry_repositories_uses_retry_helper():
    client = MagicMock()
    location_request = MagicMock()
    repository_request = MagicMock()
    next_repository_request = MagicMock()
    locations = client.projects.return_value.locations.return_value
    locations.list.return_value = location_request
    locations.list_next.return_value = None
    repositories = (
        client.projects.return_value.locations.return_value.repositories.return_value
    )
    repositories.list.return_value = repository_request
    repositories.list_next.side_effect = [next_repository_request, None]

    location_request.execute.return_value = {
        "locations": [{"locationId": "us-central1"}]
    }
    repository_request.execute.return_value = {"repositories": [{"name": "repo-1"}]}
    next_repository_request.execute.return_value = {
        "repositories": [{"name": "repo-2"}]
    }

    result = get_artifact_registry_repositories(client, "test-project")

    assert result == [{"name": "repo-1"}, {"name": "repo-2"}]
    repository_request.execute.assert_called_once_with(
        num_retries=GCP_API_NUM_RETRIES,
    )
    next_repository_request.execute.assert_called_once_with(
        num_retries=GCP_API_NUM_RETRIES,
    )
