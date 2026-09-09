from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

from cartography.intel.socketdev.repositories import get


@patch("cartography.intel.socketdev.repositories.requests.Session")
def test_get_fetches_missing_integration_metadata(mock_session_class: Mock) -> None:
    mock_session = mock_session_class.return_value
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
    detail_response.json.return_value = {
        "id": "socket-repo",
        "slug": "service",
        "integration_meta": {
            "type": "github",
            "value": {
                "installation_login": "example",
                "repo_name": "service",
            },
        },
    }
    mock_session.get.side_effect = [list_response, detail_response]

    repositories = get("token", "socket-org")

    assert repositories == [
        {**missing_metadata, **detail_response.json.return_value},
        existing_metadata,
    ]
    assert mock_session.get.call_args_list == [
        call(
            "https://api.socket.dev/v0/orgs/socket-org/repos",
            params={"per_page": 100, "page": 1},
            timeout=(60, 60),
        ),
        call(
            "https://api.socket.dev/v0/orgs/socket-org/repos/service",
            params={"workspace": "example"},
            timeout=(60, 60),
        ),
    ]
