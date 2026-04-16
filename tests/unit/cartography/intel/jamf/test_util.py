from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.jamf.util import call_jamf_api
from cartography.intel.jamf.util import create_jamf_api_session


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
    )
