from unittest.mock import MagicMock

import pytest

from cartography.intel.nullify.util import build_base_url
from cartography.intel.nullify.util import NullifyEnvelopeError
from cartography.intel.nullify.util import paginate


def test_build_base_url_default():
    assert build_base_url("acme") == "https://api.acme.nullify.ai"


def test_build_base_url_override_strips_trailing_slash():
    assert build_base_url("acme", "https://api.test.local/") == "https://api.test.local"


def _mock_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_paginate_follows_next_token():
    api_session = MagicMock()
    api_session.get.side_effect = [
        _mock_response({"items": [{"id": "1"}], "nextToken": "abc"}),
        _mock_response({"items": [{"id": "2"}], "nextToken": ""}),
    ]

    result = paginate(api_session, "https://api.acme.nullify.ai/x", "items")

    assert result == [{"id": "1"}, {"id": "2"}]
    assert api_session.get.call_count == 2
    # The second request carries the cursor from the first response.
    _, second_kwargs = api_session.get.call_args_list[1]
    assert second_kwargs["params"]["nextToken"] == "abc"


def test_paginate_single_page_when_no_next_token():
    # Endpoints like /admin/users omit nextToken entirely -> a single request.
    api_session = MagicMock()
    api_session.get.side_effect = [
        _mock_response({"users": [{"id": "U1"}, {"id": "U2"}]}),
    ]

    result = paginate(api_session, "https://api.acme.nullify.ai/admin/users", "users")

    assert result == [{"id": "U1"}, {"id": "U2"}]
    assert api_session.get.call_count == 1


def test_paginate_matches_key_case_insensitively():
    # A case mismatch (e.g. "Users" vs "users") must NOT yield an empty list, otherwise a
    # subsequent cleanup would delete all previously-ingested nodes.
    api_session = MagicMock()
    api_session.get.side_effect = [
        _mock_response({"Users": [{"id": "U1"}]}),
    ]

    result = paginate(api_session, "https://api.acme.nullify.ai/admin/users", "users")

    assert result == [{"id": "U1"}]


def test_paginate_handles_indexed_object_envelope():
    # Some collections come back as an id -> item map rather than an array.
    api_session = MagicMock()
    api_session.get.side_effect = [
        _mock_response({"repositories": {"R1": {"id": "R1"}, "R2": {"id": "R2"}}}),
    ]

    result = paginate(
        api_session, "https://api.acme.nullify.ai/admin/repositories", "repositories"
    )

    assert {r["id"] for r in result} == {"R1", "R2"}


def test_paginate_missing_key_raises():
    # A missing collection key means a malformed/changed envelope. It must raise, NOT
    # return [] - otherwise the caller's cleanup would delete all prior nodes.
    api_session = MagicMock()
    api_session.get.side_effect = [_mock_response({"version": "1"})]

    with pytest.raises(NullifyEnvelopeError):
        paginate(api_session, "https://api.acme.nullify.ai/x", "repositories")


def test_paginate_null_collection_is_empty():
    # A present-but-null collection (nullable array) is a legitimately-empty page.
    api_session = MagicMock()
    api_session.get.side_effect = [_mock_response({"repositories": None})]

    result = paginate(
        api_session, "https://api.acme.nullify.ai/admin/repositories", "repositories"
    )

    assert result == []
