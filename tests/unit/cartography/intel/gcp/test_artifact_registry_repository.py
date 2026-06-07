from types import SimpleNamespace
from unittest.mock import MagicMock

from google.api_core.exceptions import PermissionDenied

from cartography.intel.gcp.artifact_registry.repository import (
    get_artifact_registry_repositories,
)


def test_get_artifact_registry_repositories_uses_gapic_client(monkeypatch):
    client = MagicMock()
    client.list_repositories.side_effect = [
        [SimpleNamespace(name="repo-1")],
        [SimpleNamespace(name="repo-2")],
    ]
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_locations",
        lambda _client, _project_id: ["us-central1", "us-east1"],
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.proto_message_to_dict",
        lambda repo: {"name": repo.name},
    )

    result = get_artifact_registry_repositories(
        client,
        "test-project",
        max_workers=1,
    )

    assert result.repositories == [{"name": "repo-1"}, {"name": "repo-2"}]
    assert result.cleanup_safe is True
    client.list_repositories.assert_any_call(
        parent="projects/test-project/locations/us-central1"
    )
    client.list_repositories.assert_any_call(
        parent="projects/test-project/locations/us-east1"
    )


def test_get_artifact_registry_repositories_location_failure_is_not_cleanup_safe(
    monkeypatch,
):
    client = MagicMock()
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_locations",
        lambda _client, _project_id: None,
    )

    result = get_artifact_registry_repositories(client, "test-project")

    assert result.repositories == []
    assert result.cleanup_safe is False
    client.list_repositories.assert_not_called()


def test_get_artifact_registry_repositories_permission_denied_skips_cleanup(
    monkeypatch,
):
    client = MagicMock()
    client.list_repositories.side_effect = PermissionDenied("denied")
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_locations",
        lambda _client, _project_id: ["us-central1"],
    )

    result = get_artifact_registry_repositories(
        client,
        "test-project",
        max_workers=1,
    )

    assert result.repositories == []
    assert result.cleanup_safe is False
