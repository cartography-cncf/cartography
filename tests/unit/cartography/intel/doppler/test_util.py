from unittest.mock import Mock

import pytest

from cartography.intel.doppler.util import paginated_get


def _session(pages):
    """Build a fake requests.Session whose .get() returns the given page bodies in order."""
    responses = []
    for body in pages:
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.json = Mock(return_value=body)
        responses.append(resp)
    session = Mock()
    session.get = Mock(side_effect=responses)
    return session


def test_paginated_get_single_page():
    session = _session([{"projects": [{"slug": "a"}, {"slug": "b"}]}])
    assert paginated_get(session, "http://x/projects", "projects") == [
        {"slug": "a"},
        {"slug": "b"},
    ]


def test_paginated_get_empty_list_is_ok():
    # An explicitly empty list is a valid "no items" response, not an error.
    session = _session([{"projects": []}])
    assert paginated_get(session, "http://x/projects", "projects") == []


def test_paginated_get_missing_key_raises():
    # A response missing the expected key must fail fast rather than silently
    # returning [] (which would let cleanup delete a populated node type).
    session = _session([{"unexpected": []}])
    with pytest.raises(ValueError, match="missing the expected 'projects' key"):
        paginated_get(session, "http://x/projects", "projects")
