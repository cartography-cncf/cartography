from unittest import mock

import pytest
import requests

import cartography.intel.civo.sshkeys


def _make_response(payload):
    resp = mock.MagicMock(spec=requests.Response)
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_transform_ssh_keys_keeps_fields() -> None:
    ssh_keys = cartography.intel.civo.sshkeys.transform_ssh_keys(
        [{"id": "key-1", "name": "laptop", "fingerprint": "aa:bb:cc"}]
    )

    assert ssh_keys == [
        {"id": "key-1", "name": "laptop", "fingerprint": "aa:bb:cc"},
    ]


def test_transform_ssh_keys_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="missing required non-empty ssh key id"):
        cartography.intel.civo.sshkeys.transform_ssh_keys(
            [{"id": "", "name": "laptop", "fingerprint": "aa:bb:cc"}]
        )


def test_sshkeys_get_reads_bare_array() -> None:
    # Live-tested against a real Civo account: GET /v2/sshkeys returns a
    # bare JSON array, not the paginated wrapper this module originally
    # (incorrectly) assumed.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([{"id": "key-1"}])]

    results = cartography.intel.civo.sshkeys.get(session, "https://api.civo.com")

    assert results == [{"id": "key-1"}]
