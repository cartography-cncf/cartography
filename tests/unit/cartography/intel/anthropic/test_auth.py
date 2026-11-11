from unittest.mock import MagicMock

import requests

import cartography.intel.anthropic.auth
from cartography.intel.anthropic.auth import WorkloadIdentityAuth
from cartography.intel.anthropic.auth import WorkloadIdentityFederation


def _token_response(access_token: str, expires_in: int) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
    }
    return response


def _authorize(auth: WorkloadIdentityAuth) -> str:
    request = requests.Request("GET", "https://api.anthropic.com/v1/x").prepare()
    return auth(request).headers["Authorization"]


def test_exchanges_the_current_identity_token_once_per_access_token(tmp_path, mocker):
    token_file = tmp_path / "token"
    token_file.write_text("jwt-1\n")
    clock = mocker.patch.object(
        cartography.intel.anthropic.auth.time, "monotonic", return_value=0.0
    )
    post = mocker.patch.object(
        cartography.intel.anthropic.auth.requests,
        "post",
        side_effect=[
            _token_response("sk-ant-oat01-first", 60),
            _token_response("sk-ant-oat01-second", 60),
        ],
    )
    auth = WorkloadIdentityAuth(
        WorkloadIdentityFederation(
            identity_token_file=str(token_file),
            federation_rule_id="fdrl_test",
            organization_id="00000000-0000-0000-0000-000000000000",
            service_account_id="svac_test",
        ),
    )

    assert _authorize(auth) == "Bearer sk-ant-oat01-first"
    clock.return_value = 40.0
    assert _authorize(auth) == "Bearer sk-ant-oat01-first"

    token_file.write_text("jwt-2\n")
    clock.return_value = 50.0
    assert _authorize(auth) == "Bearer sk-ant-oat01-second"

    assert [call.kwargs["json"] for call in post.call_args_list] == [
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
            "federation_rule_id": "fdrl_test",
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "service_account_id": "svac_test",
        }
        for assertion in ("jwt-1", "jwt-2")
    ]
