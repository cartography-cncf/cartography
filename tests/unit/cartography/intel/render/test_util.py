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
from cartography.intel.render.util import list_plain_array

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


def test_list_plain_array_returns_items_unpaginated():
    session = Mock()
    session.get.return_value = _response([{"userId": "usr-1"}, {"userId": "usr-2"}])

    items = list_plain_array(session, URL)

    assert items == [{"userId": "usr-1"}, {"userId": "usr-2"}]
    assert session.get.call_count == 1


def test_list_plain_array_raises_on_non_list_response():
    session = Mock()
    session.get.return_value = _response({"error": "not found"})

    with pytest.raises(ValueError):
        list_plain_array(session, URL)


def test_list_plain_array_raises_on_non_object_entry():
    session = Mock()
    session.get.return_value = _response(["not-an-object"])

    with pytest.raises(ValueError):
        list_plain_array(session, URL)


def test_list_plain_array_never_paginates():
    """
    Render documents cursor as an opaque token that is a sibling of each resource in
    the wrapped `{resource_key: {...}, cursor}` shape list_paginated() handles - but
    bare-array endpoints (workspace members, registry credentials, disk snapshots)
    return no cursor value anywhere in the response, so there is no documented way to
    know what to pass as the next page's `cursor`. A prior version of this function
    guessed the last item's own `id`, but Render's pagination docs are explicit that
    cursor is not derived from a resource's id - that guess could silently send an
    invalid cursor or skip/duplicate data. A single unpaginated GET is the only
    behavior this endpoint shape can support correctly; a full page here is returned
    as-is rather than triggering another (unfoundedly-cursored) request.
    """
    full_page = [{"id": f"usr-{i}"} for i in range(100)]
    session = Mock()
    session.get.return_value = _response(full_page)

    items = list_plain_array(session, URL)

    assert len(items) == 100
    assert session.get.call_count == 1


def test_list_plain_array_passes_limit_through_as_a_query_param():
    session = Mock()
    session.get.return_value = _response([{"id": "crd-1"}])

    list_plain_array(session, URL, limit=100)

    assert session.get.call_args.kwargs["params"]["limit"] == 100


def test_list_plain_array_raises_when_a_full_page_could_hide_more_items():
    """
    Some bare-array endpoints document a `limit` query param with a default page size
    below the account's plausible inventory (e.g. registry credentials defaults to 20,
    max 100 - see registrycredentials.py). If a response comes back exactly `limit`
    items long, that's genuinely ambiguous between "the account has exactly this many"
    and "there are more we have no documented way to fetch" (no cursor exists on this
    response shape - see test_list_plain_array_never_paginates). Silently returning a
    possibly-truncated inventory here would let the caller's scoped cleanup delete
    every real resource past this page, so this must raise instead of guessing.
    """
    session = Mock()
    session.get.return_value = _response([{"id": f"crd-{i}"} for i in range(100)])

    with pytest.raises(ValueError):
        list_plain_array(session, URL, limit=100)


def test_list_plain_array_does_not_raise_when_under_the_limit():
    session = Mock()
    session.get.return_value = _response([{"id": f"crd-{i}"} for i in range(99)])

    items = list_plain_array(session, URL, limit=100)

    assert len(items) == 99
