from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.jamf.util import call_jamf_api
from cartography.intel.jamf.util import JamfClientCredentialsAuth
from cartography.intel.jamf.util import create_jamf_api_session
from cartography.intel.jamf.util import get_paginated_jamf_results


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_prefers_bearer_token(mock_session_class: Mock) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    token_response = Mock(ok=True, status_code=200)
    token_response.json.return_value = {"token": "test-token"}
    mock_session.post.return_value = token_response
    mock_session_class.return_value = mock_session

    session = create_jamf_api_session(
        "https://test.jamfcloud.com/JSSResource",
        "test-user",
        "test-password",
    )

    assert session is mock_session
    assert mock_session.headers["Accept"] == "application/json"
    assert mock_session.headers["Authorization"] == "Bearer test-token"
    mock_session.post.assert_called_once()
    assert (
        mock_session.post.call_args.args[0]
        == "https://test.jamfcloud.com/api/v1/auth/token"
    )
    assert isinstance(
        mock_session.post.call_args.kwargs["auth"],
        requests.auth.HTTPBasicAuth,
    )
    assert "auth" not in mock_session.__dict__


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_falls_back_to_basic_auth(
    mock_session_class: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    token_response = Mock(ok=False, status_code=404)
    mock_session.post.return_value = token_response
    mock_session_class.return_value = mock_session

    session = create_jamf_api_session(
        "https://test.jamfcloud.com/JSSResource",
        "test-user",
        "test-password",
    )

    assert session is mock_session
    assert mock_session.headers == {"Accept": "application/json"}
    assert isinstance(mock_session.auth, requests.auth.HTTPBasicAuth)


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_falls_back_to_basic_auth_on_405(
    mock_session_class: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    token_response = Mock(ok=False, status_code=405)
    mock_session.post.return_value = token_response
    mock_session_class.return_value = mock_session

    session = create_jamf_api_session(
        "https://test.jamfcloud.com/JSSResource",
        "test-user",
        "test-password",
    )

    assert session is mock_session
    assert isinstance(mock_session.auth, requests.auth.HTTPBasicAuth)


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_closes_session_on_timeout(
    mock_session_class: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    mock_session.post.side_effect = requests.exceptions.Timeout()
    mock_session_class.return_value = mock_session

    with pytest.raises(requests.exceptions.Timeout):
        create_jamf_api_session(
            "https://test.jamfcloud.com/JSSResource",
            "test-user",
            "test-password",
        )

    mock_session.close.assert_called_once_with()


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_closes_session_on_http_error(
    mock_session_class: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    token_response = Mock(ok=False, status_code=401)
    token_response.raise_for_status.side_effect = requests.HTTPError("unauthorized")
    mock_session.post.return_value = token_response
    mock_session_class.return_value = mock_session

    with pytest.raises(requests.HTTPError, match="unauthorized"):
        create_jamf_api_session(
            "https://test.jamfcloud.com/JSSResource",
            "test-user",
            "test-password",
        )

    mock_session.close.assert_called_once_with()


def test_call_jamf_api_normalizes_trailing_slashes() -> None:
    mock_session = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"computer_groups": []}
    mock_session.get.return_value = mock_response

    call_jamf_api(
        "/computergroups",
        "https://test.jamfcloud.com/JSSResource/",
        mock_session,
    )

    mock_session.get.assert_called_once_with(
        "https://test.jamfcloud.com/JSSResource/computergroups",
        timeout=(60, 60),
        params=None,
    )


def test_call_jamf_api_appends_classic_api_path_for_plain_host() -> None:
    mock_session = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"computer_groups": []}
    mock_session.get.return_value = mock_response

    call_jamf_api(
        "/computergroups",
        "https://test.jamfcloud.com",
        mock_session,
    )

    mock_session.get.assert_called_once_with(
        "https://test.jamfcloud.com/JSSResource/computergroups",
        timeout=(60, 60),
        params=None,
    )


def test_call_jamf_api_uses_instance_uri_for_modern_api_paths() -> None:
    mock_session = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"results": [], "totalCount": 0}
    mock_session.get.return_value = mock_response

    call_jamf_api(
        "/api/v1/groups",
        "https://test.jamfcloud.com/JSSResource/",
        mock_session,
    )

    mock_session.get.assert_called_once_with(
        "https://test.jamfcloud.com/api/v1/groups",
        timeout=(60, 60),
        params=None,
    )


def test_get_paginated_jamf_results_collects_all_pages() -> None:
    mock_session = Mock()
    first_page_response = Mock()
    first_page_response.json.return_value = {
        "results": [{"id": 1}, {"id": 2}],
        "totalCount": 3,
    }
    second_page_response = Mock()
    second_page_response.json.return_value = {
        "results": [{"id": 3}],
        "totalCount": 3,
    }
    mock_session.get.side_effect = [first_page_response, second_page_response]

    results = get_paginated_jamf_results(
        "/api/v1/groups",
        "https://test.jamfcloud.com",
        mock_session,
    )

    assert results == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert mock_session.get.call_count == 2
    assert mock_session.get.call_args_list[0].kwargs["params"] == {
        "page": 0,
        "page-size": 100,
    }
    assert mock_session.get.call_args_list[1].kwargs["params"] == {
        "page": 1,
        "page-size": 100,
    }


def _token_response(token: str, expires_in: int = 60) -> Mock:
    response = Mock(ok=True, status_code=200)
    response.json.return_value = {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": expires_in,
    }
    return response


@patch("cartography.intel.jamf.util.requests.post")
@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_uses_api_client(
    mock_session_class: Mock,
    mock_post: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    mock_session_class.return_value = mock_session
    mock_post.return_value = _token_response("client-token")

    session = create_jamf_api_session(
        "https://test.jamfcloud.com/JSSResource",
        jamf_user="test-user",
        jamf_password="test-password",
        jamf_client_id="test-client-id",
        jamf_client_secret="test-client-secret",
    )

    assert session is mock_session
    assert isinstance(mock_session.auth, JamfClientCredentialsAuth)
    # The user/password token endpoint is never called when a client is set.
    mock_session.post.assert_not_called()
    mock_post.assert_called_once_with(
        "https://test.jamfcloud.com/api/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        },
        timeout=(60, 60),
    )


@patch("cartography.intel.jamf.util.requests.post")
@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_closes_session_on_bad_api_client(
    mock_session_class: Mock,
    mock_post: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    mock_session_class.return_value = mock_session
    response = Mock(ok=False, status_code=401)
    response.raise_for_status.side_effect = requests.HTTPError("unauthorized")
    mock_post.return_value = response

    with pytest.raises(requests.HTTPError, match="unauthorized"):
        create_jamf_api_session(
            "https://test.jamfcloud.com",
            jamf_client_id="test-client-id",
            jamf_client_secret="wrong-secret",
        )

    mock_session.close.assert_called_once_with()


@patch("cartography.intel.jamf.util.requests.Session")
def test_create_jamf_api_session_requires_credentials(
    mock_session_class: Mock,
) -> None:
    mock_session = Mock()
    mock_session.headers = {}
    mock_session_class.return_value = mock_session

    with pytest.raises(ValueError):
        create_jamf_api_session(
            "https://test.jamfcloud.com",
            jamf_client_id="test-client-id",
        )

    mock_session.close.assert_called_once_with()


@patch("cartography.intel.jamf.util.time.monotonic")
@patch("cartography.intel.jamf.util.requests.post")
def test_api_client_auth_refreshes_expiring_token(
    mock_post: Mock,
    mock_monotonic: Mock,
) -> None:
    mock_post.side_effect = [
        _token_response("first-token", expires_in=60),
        _token_response("second-token", expires_in=60),
    ]
    auth = JamfClientCredentialsAuth(
        "https://test.jamfcloud.com",
        "test-client-id",
        "test-client-secret",
    )

    mock_monotonic.return_value = 1000.0
    first = auth(requests.Request("GET", "https://test.jamfcloud.com/x").prepare())
    assert first.headers["Authorization"] == "Bearer first-token"

    # Still well inside the lifetime: the token is reused.
    mock_monotonic.return_value = 1010.0
    reused = auth(requests.Request("GET", "https://test.jamfcloud.com/x").prepare())
    assert reused.headers["Authorization"] == "Bearer first-token"
    assert mock_post.call_count == 1

    # Within the refresh margin of expiry: a new token is fetched.
    mock_monotonic.return_value = 1040.0
    refreshed = auth(
        requests.Request("GET", "https://test.jamfcloud.com/x").prepare(),
    )
    assert refreshed.headers["Authorization"] == "Bearer second-token"
    assert mock_post.call_count == 2
