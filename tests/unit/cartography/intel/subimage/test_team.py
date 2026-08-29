from unittest.mock import MagicMock

from cartography.intel.subimage.team import get


def test_get_reads_page_envelope():
    # Regression: GET /api/team/members returns the Page[T] envelope
    # ({"items": [...]}); get() must unwrap it, not iterate the dict keys.
    api_session = MagicMock()
    api_session.get.return_value.json.return_value = {
        "items": [{"id": "member-1"}],
        "total_count": 1,
        "limit": 100,
        "offset": 0,
    }

    assert get(api_session, "https://app.example.com") == [{"id": "member-1"}]


def test_get_paginates_all_pages():
    # Regression: get() must walk every page, not just the first, or cleanup
    # would delete members living on later pages.
    api_session = MagicMock()
    api_session.get.return_value.json.side_effect = [
        {
            "items": [{"id": "member-1"}, {"id": "member-2"}],
            "total_count": 3,
            "limit": 2,
        },
        {"items": [{"id": "member-3"}], "total_count": 3, "limit": 2},
    ]

    assert get(api_session, "https://app.example.com") == [
        {"id": "member-1"},
        {"id": "member-2"},
        {"id": "member-3"},
    ]
    assert api_session.get.call_count == 2
