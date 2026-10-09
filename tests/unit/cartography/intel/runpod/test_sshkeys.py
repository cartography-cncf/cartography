from unittest.mock import Mock

import pytest

from cartography.intel.runpod.sshkeys import get
from cartography.intel.runpod.sshkeys import transform

ACCOUNT_ID = "runpod-test-account"
PUBLIC_KEY = "ssh-rsa AQID laptop@example"
FINGERPRINT = "SHA256:A5BYxvLAy0ksUzsKTRTvd8wPeKvMztUofYShogEc+4E"


def _response(body):
    mock_response = Mock()
    mock_response.json.return_value = body
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_get_unwraps_documented_keys_response():
    session = Mock()
    session.get.return_value = _response({"keys": [PUBLIC_KEY]})

    rows = get(session, "https://api.runpod.io/v2")

    assert rows == [PUBLIC_KEY]
    session.get.assert_called_once_with(
        "https://api.runpod.io/v2/account/ssh-keys",
        timeout=(60, 60),
    )


def test_transform_uses_stable_fingerprint_for_documented_string_key():
    rows = transform([PUBLIC_KEY], ACCOUNT_ID)

    assert rows == [
        {
            "id": FINGERPRINT,
            "account_id": ACCOUNT_ID,
            "name": None,
            "fingerprint": FINGERPRINT,
            "created_at": None,
        }
    ]


def test_transform_uses_stable_fingerprint_when_object_id_is_missing():
    rows = transform([{"publicKey": PUBLIC_KEY, "comment": "laptop"}], ACCOUNT_ID)

    assert rows[0]["id"] == FINGERPRINT
    assert rows[0]["name"] is None
    assert rows[0]["fingerprint"] == FINGERPRINT


def test_transform_prefers_provider_id_when_present():
    rows = transform(
        [
            {
                "id": "sshkey-1",
                "publicKey": PUBLIC_KEY,
                "comment": "laptop",
            }
        ],
        ACCOUNT_ID,
    )

    assert rows[0]["id"] == "sshkey-1"
    assert rows[0]["fingerprint"] == FINGERPRINT


def test_transform_rejects_key_without_id_or_valid_fingerprint():
    with pytest.raises(ValueError):
        transform(["not-valid"], ACCOUNT_ID)
