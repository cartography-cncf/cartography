from unittest.mock import MagicMock

from cartography.intel.gcp.artifact_registry.repository import (
    get_artifact_registry_repositories,
)


def test_get_artifact_registry_repositories_uses_retry_helper(monkeypatch):
    client = MagicMock()
    request = MagicMock()
    next_request = MagicMock()
    repositories = (
        client.projects.return_value.locations.return_value.repositories.return_value
    )
    repositories.list.return_value = request
    repositories.list_next.side_effect = [next_request, None]

    calls: list[MagicMock] = []

    def _fake_execute(req):
        calls.append(req)
        if req is request:
            return {"repositories": [{"name": "repo-1"}]}
        return {"repositories": [{"name": "repo-2"}]}

    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.get_artifact_registry_locations",
        lambda _client, _project_id: ["us-central1"],
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.repository.gcp_api_execute_with_retry",
        _fake_execute,
    )

    result = get_artifact_registry_repositories(client, "test-project")

    assert result == [{"name": "repo-1"}, {"name": "repo-2"}]
    assert calls == [request, next_request]
