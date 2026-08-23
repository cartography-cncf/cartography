"""
A page that comes back full must be followed by another request for the next page.

Render's list endpoints return one page per call; if `list_paginated()` stopped after the
first full page, an account with more resources of a type than fit on one page would look
identical (to a caller's scoped cleanup) to one with only that many resources, silently
losing everything past the first page.
"""

from unittest.mock import Mock

import pytest

from cartography.intel.render.util import list_paginated

URL = "https://api.render.com/v1/services"


def _response(body):
    mock_response = Mock()
    mock_response.json.return_value = body
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_list_paginated_follows_cursor_across_a_full_page():
    page_1 = [{"service": {"id": f"srv-{i}"}, "cursor": f"srv-{i}"} for i in range(100)]
    page_2 = [{"service": {"id": "srv-100"}, "cursor": "srv-100"}]
    session = Mock()
    session.get.side_effect = [_response(page_1), _response(page_2)]

    items = list_paginated(session, URL, "service")

    assert [item["id"] for item in items] == [f"srv-{i}" for i in range(100)] + [
        "srv-100"
    ]
    assert session.get.call_count == 2
    first_call_params = session.get.call_args_list[0].kwargs["params"]
    second_call_params = session.get.call_args_list[1].kwargs["params"]
    assert "cursor" not in first_call_params
    assert second_call_params["cursor"] == "srv-99"


def test_list_paginated_stops_after_a_short_page():
    session = Mock()
    session.get.side_effect = [
        _response([{"service": {"id": "srv-0"}, "cursor": "srv-0"}]),
    ]

    items = list_paginated(session, URL, "service")

    assert [item["id"] for item in items] == ["srv-0"]
    assert session.get.call_count == 1


def test_list_paginated_raises_on_non_list_response():
    session = Mock()
    session.get.return_value = _response({"error": "not found"})

    with pytest.raises(ValueError):
        list_paginated(session, URL, "service")


def test_list_paginated_raises_on_entries_missing_the_resource_key():
    session = Mock()
    session.get.return_value = _response([{"cursor": "srv-0"}])

    with pytest.raises(ValueError):
        list_paginated(session, URL, "service")


def test_list_paginated_raises_on_non_object_resource_value():
    session = Mock()
    session.get.return_value = _response(
        [{"secretFile": "not-an-object", "cursor": "x"}]
    )

    with pytest.raises(ValueError):
        list_paginated(session, URL, "secretFile")


def test_list_paginated_malformed_entry_error_never_embeds_entry_values():
    """
    A malformed entry's raised error must report only structural info (keys/types),
    never the entry's raw values - some resource_key values (e.g. "secretFile") wrap
    plaintext secret content, which must never end up in an exception message that
    could get logged.
    """
    secret_value = "SUPER_SECRET_VALUE=do-not-leak-me"
    session = Mock()
    session.get.return_value = _response(
        [{"cursor": "x", "unexpectedField": secret_value}]
    )

    with pytest.raises(ValueError) as exc_info:
        list_paginated(session, URL, "secretFile")

    assert secret_value not in str(exc_info.value)


def test_list_paginated_raises_on_full_page_missing_a_trailing_cursor():
    """
    A full page whose last entry has no cursor is ambiguous, not evidence of the list's
    end: every entry observed live carries a cursor regardless of position. Silently
    stopping here would let a malformed/changed response shape masquerade as "the
    inventory has exactly _PAGE_LIMIT items", and the caller's scoped cleanup would then
    delete every real node past this page.
    """
    full_page = [
        {"service": {"id": f"srv-{i}"}, "cursor": f"srv-{i}"} for i in range(99)
    ] + [
        {"service": {"id": "srv-99"}}
    ]  # last entry has no cursor
    session = Mock()
    session.get.return_value = _response(full_page)

    with pytest.raises(ValueError):
        list_paginated(session, URL, "service")


def test_list_paginated_raises_on_a_repeated_cursor_instead_of_looping_forever():
    """
    A full page whose last entry's cursor repeats the previous page's cursor can never
    legitimately advance pagination - looping on it would hang the sync instead of
    surfacing the bad response.
    """
    repeating_page = [
        {"service": {"id": f"srv-{i}"}, "cursor": "srv-99"} for i in range(100)
    ]
    session = Mock()
    session.get.return_value = _response(repeating_page)

    with pytest.raises(ValueError):
        list_paginated(session, URL, "service")
