from datetime import datetime
from datetime import timedelta
from datetime import timezone
from email.utils import format_datetime
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

import cartography.intel.anthropic.auth
from cartography.intel.anthropic.auth import WorkloadIdentityAuth
from cartography.intel.anthropic.auth import WorkloadIdentityFederation

API_URL = "https://api.anthropic.com/v1/organizations/users"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _token_response(
    status_code: int, access_token: str = "", retry_after: str = "30"
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"retry-after": retry_after} if status_code == 429 else {}
    response.raise_for_status.side_effect = (
        requests.HTTPError(response=response) if status_code >= 400 else None
    )
    response.json.return_value = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 60,
    }
    return response


class _AnthropicApi(HTTPAdapter):
    """Accepts only the bearer tokens it is told are live."""

    def __init__(self, live_tokens: set[str]) -> None:
        super().__init__()
        self.live_tokens = live_tokens
        self.seen: list[str] = []

    def send(self, request, **kwargs):
        self.seen.append(request.headers["Authorization"])
        response = requests.Response()
        response.request = request
        response.connection = self
        response._content = b""
        response.status_code = (
            200
            if request.headers["Authorization"].removeprefix("Bearer ")
            in self.live_tokens
            else 401
        )
        return response


def _session(auth: WorkloadIdentityAuth, api: _AnthropicApi) -> requests.Session:
    session = requests.Session()
    session.mount("https://", api)
    session.auth = auth
    return session


def _auth(token_file) -> WorkloadIdentityAuth:
    return WorkloadIdentityAuth(
        WorkloadIdentityFederation(
            identity_token_file=str(token_file),
            federation_rule_id="fdrl_test",
            organization_id="00000000-0000-0000-0000-000000000000",
            service_account_id="svac_test",
            workspace_id="wrkspc_test",
        ),
    )


def _exchanged_assertions(post: MagicMock) -> list[str]:
    return [call.kwargs["json"]["assertion"] for call in post.call_args_list]


def test_exchanges_again_only_once_the_identity_token_rotates(tmp_path, mocker):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    clock = mocker.patch.object(
        cartography.intel.anthropic.auth.time, "monotonic", return_value=0.0
    )
    post = mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=[_token_response(200, "first"), _token_response(200, "second")],
    )
    api = _AnthropicApi({"first", "second"})
    session = _session(_auth(token_file), api)

    session.get(API_URL)
    clock.return_value = 45.0
    session.get(API_URL)
    token_file.write_text("jwt-2\n")
    session.get(API_URL)

    assert api.seen == ["Bearer first", "Bearer first", "Bearer second"]
    assert post.call_args_list[0].kwargs["json"] == {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": "jwt-1",
        "federation_rule_id": "fdrl_test",
        "organization_id": "00000000-0000-0000-0000-000000000000",
        "service_account_id": "svac_test",
        "workspace_id": "wrkspc_test",
    }
    assert _exchanged_assertions(post) == ["jwt-1", "jwt-2"]


@pytest.mark.parametrize(
    ("rotated", "status_code", "seen"),
    [
        (True, 200, ["Bearer expired", "Bearer fresh"]),
        (False, 401, ["Bearer expired"]),
    ],
)
def test_a_rejected_access_token_is_replaced_only_with_a_new_identity_token(
    rotated, status_code, seen, tmp_path, mocker
):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    post = mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=[_token_response(200, "expired"), _token_response(200, "fresh")],
    )
    auth = _auth(token_file)
    api = _AnthropicApi({"fresh"})
    session = _session(auth, api)
    original_send = api.send

    def send_then_rotate(request, **kwargs):
        response = original_send(request, **kwargs)
        if rotated:
            token_file.write_text("jwt-2\n")
        return response

    api.send = send_then_rotate

    response = session.get(API_URL)

    assert response.status_code == status_code
    assert api.seen == seen
    assert _exchanged_assertions(post) == (["jwt-1", "jwt-2"] if rotated else ["jwt-1"])


@pytest.mark.parametrize(
    "retry_after",
    [
        "30",
        format_datetime(NOW + timedelta(seconds=30), True),
    ],
    ids=["seconds", "http-date"],
)
def test_a_retried_exchange_sends_the_current_identity_token(
    retry_after, tmp_path, mocker
):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    sleep = mocker.patch.object(cartography.intel.anthropic.auth.time, "sleep")
    mocker.patch.object(
        cartography.intel.anthropic.auth, "datetime", wraps=datetime
    ).now.return_value = NOW

    responses = iter(
        [_token_response(429, retry_after=retry_after), _token_response(200, "first")]
    )

    def rotate_while_throttled(*args, **kwargs):
        response = next(responses)
        token_file.write_text("jwt-2\n")
        return response

    post = mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=rotate_while_throttled,
    )

    _session(_auth(token_file), _AnthropicApi({"first"})).get(API_URL)

    assert _exchanged_assertions(post) == ["jwt-1", "jwt-2"]
    sleep.assert_called_once_with(30.0)


def test_a_refused_replay_after_a_server_error_reports_the_server_error(
    tmp_path, mocker
):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    mocker.patch.object(cartography.intel.anthropic.auth.time, "sleep")
    mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=[_token_response(503), _token_response(400)],
    )

    with pytest.raises(requests.HTTPError) as error:
        _session(_auth(token_file), _AnthropicApi(set())).get(API_URL)

    assert error.value.response.status_code == 503
