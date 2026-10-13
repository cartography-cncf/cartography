from unittest.mock import call
from unittest.mock import Mock

import cartography.intel.socketdev.repositories as repositories


def test_get_fetches_missing_integration_metadata(mocker) -> None:
    list_session = mocker.MagicMock()
    detail_session = mocker.MagicMock()
    mocker.patch.object(
        repositories,
        "_create_session",
        side_effect=[list_session, detail_session],
    )
    list_session.__enter__.return_value = list_session
    detail_session.__enter__.return_value = detail_session
    list_response = Mock()
    missing_metadata = {
        "id": "socket-repo",
        "slug": "service",
        "workspace": "example",
    }
    existing_metadata = {
        "id": "socket-repo-2",
        "slug": "worker",
        "integration_meta": None,
    }
    list_response.json.return_value = {
        "results": [
            missing_metadata,
            existing_metadata,
        ],
        "nextPage": None,
    }
    detail_response = Mock()
    detail_response.status_code = 200
    detail_response.json.return_value = {
        "workspace": None,
        "integration_meta": {
            "type": "github",
            "value": {
                "installation_login": "example",
                "repo_name": "service",
            },
        },
    }
    list_session.get.return_value = list_response
    detail_session.get.return_value = detail_response

    result, incomplete_repository_ids = repositories.get("token", "socket-org")

    assert result == [
        {
            **missing_metadata,
            "integration_meta": detail_response.json.return_value["integration_meta"],
        },
        existing_metadata,
    ]
    assert incomplete_repository_ids == set()
    list_session.get.assert_called_once_with(
        "https://api.socket.dev/v0/orgs/socket-org/repos",
        params={"per_page": 100, "page": 1},
        timeout=(60, 60),
    )
    detail_session.get.assert_called_once_with(
        "https://api.socket.dev/v0/orgs/socket-org/repos/service",
        params={"workspace": "example"},
        timeout=(60, 60),
    )
    list_session.__exit__.assert_called_once()
    detail_session.__exit__.assert_called_once()


def test_get_keeps_list_record_when_detail_is_forbidden(mocker) -> None:
    list_session = mocker.MagicMock()
    detail_session = mocker.MagicMock()
    mocker.patch.object(
        repositories,
        "_create_session",
        side_effect=[list_session, detail_session],
    )
    list_session.__enter__.return_value = list_session
    detail_session.__enter__.return_value = detail_session
    repository = {
        "id": "socket-repo",
        "slug": "service",
        "workspace": "",
    }
    list_response = Mock()
    list_response.json.return_value = {
        "results": [repository],
        "nextPage": None,
    }
    detail_response = Mock(status_code=403)
    list_session.get.return_value = list_response
    detail_session.get.return_value = detail_response

    result, incomplete_repository_ids = repositories.get("token", "socket-org")

    assert result == [repository]
    assert incomplete_repository_ids == {"socket-repo"}
    assert detail_session.get.call_args_list[0] == call(
        "https://api.socket.dev/v0/orgs/socket-org/repos/service",
        params=None,
        timeout=(60, 60),
    )
    detail_response.raise_for_status.assert_not_called()
    list_session.__exit__.assert_called_once()
    detail_session.__exit__.assert_called_once()
