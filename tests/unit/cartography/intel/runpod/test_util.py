from unittest.mock import Mock

import pytest

from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import get_string_list
from cartography.intel.runpod.util import require_non_empty


def _response(body, json_exception=None):
    mock_response = Mock()
    if json_exception:
        mock_response.json.side_effect = json_exception
    else:
        mock_response.json.return_value = body
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_get_list_unwraps_documented_object_list_key():
    session = Mock()
    session.get.return_value = _response({"pods": [{"id": "pod-1"}]})

    records = get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))

    assert records == [{"id": "pod-1"}]


def test_get_list_accepts_legacy_plain_array_response():
    session = Mock()
    session.get.return_value = _response([{"id": "pod-1"}])

    records = get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))

    assert records == [{"id": "pod-1"}]


def test_get_list_raises_on_unexpected_object_shape():
    session = Mock()
    session.get.return_value = _response({"error": "not a list"})

    with pytest.raises(ValueError):
        get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))


def test_get_list_raises_on_non_object_entry():
    session = Mock()
    session.get.return_value = _response({"pods": ["not-an-object"]})

    with pytest.raises(ValueError):
        get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))


def test_get_list_raises_on_malformed_json():
    session = Mock()
    session.get.return_value = _response(None, ValueError("bad json"))

    with pytest.raises(ValueError, match="malformed JSON"):
        get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))


def test_get_string_list_unwraps_documented_object_string_list_key():
    session = Mock()
    session.get.return_value = _response({"keys": ["ssh-rsa AQID laptop@example"]})

    records = get_string_list(
        session,
        "https://api.runpod.io/v2",
        "/account/ssh-keys",
        ("keys",),
    )

    assert records == ["ssh-rsa AQID laptop@example"]


def test_get_string_list_raises_on_non_string_entry():
    session = Mock()
    session.get.return_value = _response({"keys": [{"id": "sshkey-1"}]})

    with pytest.raises(ValueError):
        get_string_list(
            session,
            "https://api.runpod.io/v2",
            "/account/ssh-keys",
            ("keys",),
        )


def test_require_non_empty_rejects_none_and_empty_string():
    with pytest.raises(ValueError):
        require_non_empty(None, "pod id")
    with pytest.raises(ValueError):
        require_non_empty("", "pod id")


def test_get_list_does_not_invent_undocumented_pagination():
    session = Mock()
    session.get.return_value = _response(
        {
            "pods": [{"id": "pod-1"}],
            "cursor": "opaque",
            "next": "https://api.runpod.io/v2/pods?page=2",
        }
    )

    records = get_list(session, "https://api.runpod.io/v2", "/pods", ("pods",))

    assert records == [{"id": "pod-1"}]
    assert session.get.call_count == 1
