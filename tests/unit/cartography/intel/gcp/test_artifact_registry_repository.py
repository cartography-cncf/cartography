from unittest.mock import MagicMock

from cartography.intel.gcp.artifact_registry.repository import (
    get_artifact_registry_repositories,
)


def test_get_artifact_registry_repositories_lists_all_locations(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_locations",
        lambda _client, _project_id: ["us-central1", "us-east1"],
    )

    client.list_repositories.side_effect = [
        [
            {
                "name": "projects/test-project/locations/us-central1/repositories/docker-repo",
                "format": "DOCKER",
            }
        ],
        [
            {
                "name": "projects/test-project/locations/us-east1/repositories/apt-repo",
                "format": "APT",
            }
        ],
    ]

    repositories = get_artifact_registry_repositories(client, "test-project")

    assert repositories == [
        {
            "name": "projects/test-project/locations/us-central1/repositories/docker-repo",
            "format": "DOCKER",
        },
        {
            "name": "projects/test-project/locations/us-east1/repositories/apt-repo",
            "format": "APT",
        },
    ]
    assert client.list_repositories.call_count == 2
