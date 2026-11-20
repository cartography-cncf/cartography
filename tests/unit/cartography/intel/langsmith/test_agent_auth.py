from unittest.mock import MagicMock

from cartography.intel.langsmith import agent_auth
from cartography.intel.langsmith import sso
from cartography.intel.langsmith.util import LangSmithFetchError

WORKSPACES = [{"id": "ws-a"}, {"id": "ws-b"}, {"id": "ws-c"}]


def _denied(status: int) -> LangSmithFetchError:
    return LangSmithFetchError("/v2/auth/providers", status, f"HTTP {status}")


def _provider(provider_id: str) -> dict:
    return {"id": provider_id, "provider_id": provider_id}


def test_providers_are_read_once_through_the_first_workspace_that_allows_it():
    # Arrange
    client = MagicMock()
    client.get.side_effect = [
        _denied(403),
        [_provider("org-1")],
        [_provider("platform-1")],
    ]

    # Act
    providers, complete = agent_auth.get_providers(client, "org", WORKSPACES)

    # Assert
    # Both listings are workspace-independent, so a denied workspace is not a gap.
    assert complete is True
    assert {p["id"] for p in providers} == {"org-1", "platform-1"}
    assert [c.kwargs["tenant_id"] for c in client.get.call_args_list] == [
        "ws-a",
        "ws-b",
        "ws-a",
    ]


def test_providers_are_incomplete_when_no_workspace_allows_them():
    # Arrange
    client = MagicMock()
    client.get.side_effect = _denied(403)

    # Act
    providers, complete = agent_auth.get_providers(client, "org", WORKSPACES)

    # Assert
    assert providers == []
    assert complete is False


def test_only_agents_read_in_every_workspace_count_as_read():
    # Arrange
    client = MagicMock()

    def _get(path, *, tenant_id, **_):
        if "agent-b" in path and tenant_id == "ws-b":
            raise _denied(403)
        if "agent-c" in path:
            raise LangSmithFetchError(path, 404, "HTTP 404")
        return {"data": []}

    client.get.side_effect = _get
    agents = [
        {"id": "org|agent-a", "assistant_id": "agent-a", "deployment_ids": ["d1"]},
        {
            "id": "org|agent-b",
            "assistant_id": "agent-b",
            "deployment_ids": ["d1", "d2"],
        },
        {"id": "org|agent-c", "assistant_id": "agent-c", "deployment_ids": ["d1"]},
    ]

    # Act
    _, read, complete = agent_auth.get_connections(
        client, "org", agents, {"d1": "ws-a", "d2": "ws-b"}
    )

    # Assert
    # A 404 means agent auth never saw the agent, which is a complete, empty answer.
    assert read == {"org|agent-a", "org|agent-c"}
    assert complete is False


def test_a_denied_data_plane_listing_falls_back_to_the_summary_view():
    # Arrange
    client = MagicMock()
    client.get.side_effect = [
        LangSmithFetchError("/orgs/current/data-planes", 403, "HTTP 403"),
        {"data_planes": [{"id": "dp-1", "name": "eu", "status": "READY"}]},
    ]

    # Act
    planes, complete = sso.get_data_planes(client, "org")

    # Assert
    assert complete is True
    assert [p["id"] for p in planes] == ["dp-1"]
    assert client.get.call_args_list[1].kwargs["params"] == {"view": "SUMMARY"}


def test_data_planes_are_incomplete_when_the_summary_view_is_denied_too():
    # Arrange
    client = MagicMock()
    client.get.side_effect = LangSmithFetchError(
        "/orgs/current/data-planes", 403, "HTTP 403"
    )

    # Act
    planes, complete = sso.get_data_planes(client, "org")

    # Assert
    assert planes == []
    assert complete is False


def test_a_summary_data_plane_keeps_its_stored_creation_time():
    # Arrange
    session = MagicMock()
    session.execute_read.return_value = [
        {"id": "dp-1", "created_at": "2026-02-01T09:00:00Z"}
    ]
    planes = [
        {"id": "dp-1", "name": "eu", "status": "active"},
        {"id": "dp-2", "name": "us", "status": "active"},
    ]

    # Act
    kept = sso.keep_known_created_at(session, planes, "org")

    # Assert
    assert kept == [
        {
            "id": "dp-1",
            "name": "eu",
            "status": "active",
            "created_at": "2026-02-01T09:00:00Z",
        },
        {"id": "dp-2", "name": "us", "status": "active"},
    ]
    assert session.execute_read.call_args.kwargs == {
        "ORG_ID": "org",
        "IDS": ["dp-1", "dp-2"],
    }


def test_a_full_view_data_plane_is_not_looked_up():
    # Arrange
    session = MagicMock()
    planes = [{"id": "dp-1", "created_at": "2026-02-01T09:00:00Z"}]

    # Act
    kept = sso.keep_known_created_at(session, planes, "org")

    # Assert
    assert kept == planes
    session.execute_read.assert_not_called()
