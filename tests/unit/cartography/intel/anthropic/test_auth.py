from unittest.mock import MagicMock

import requests
from requests.adapters import HTTPAdapter

import cartography.intel.anthropic.auth
from cartography.intel.anthropic.auth import WorkloadIdentityAuth
from cartography.intel.anthropic.auth import WorkloadIdentityFederation

API_URL = "https://api.anthropic.com/v1/organizations/users"


def _token_response(status_code: int, access_token: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
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


def test_a_rejected_access_token_is_replaced_and_the_request_resent(tmp_path, mocker):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=[_token_response(200, "expired"), _token_response(200, "fresh")],
    )
    api = _AnthropicApi({"fresh"})

    response = _session(_auth(token_file), api).get(API_URL)

    assert response.status_code == 200
    assert api.seen == ["Bearer expired", "Bearer fresh"]


def test_a_retried_exchange_sends_the_current_identity_token(tmp_path, mocker):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    mocker.patch.object(cartography.intel.anthropic.auth.time, "sleep")

    responses = iter([_token_response(429), _token_response(200, "first")])

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
