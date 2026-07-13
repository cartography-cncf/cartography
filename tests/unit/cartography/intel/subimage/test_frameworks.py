from unittest.mock import MagicMock

from cartography.intel.subimage.frameworks import get


def test_get_reads_page_envelope():
    # Regression: GET /api/findings/frameworks returns the Page[T] envelope
    # ({"items": [...]}), not the old {"frameworks": [...]} key.
    api_session = MagicMock()
    api_session.get.return_value.json.return_value = {
        "items": [{"id": "fw-1"}],
        "total_count": 1,
        "limit": 100,
        "offset": 0,
    }

    assert get(api_session, "https://app.example.com") == [{"id": "fw-1"}]


def test_get_paginates_all_pages():
    # Regression: get() must walk every page, not just the first, or cleanup
    # would delete frameworks living on later pages.
    api_session = MagicMock()
    api_session.get.return_value.json.side_effect = [
        {"items": [{"id": "fw-1"}, {"id": "fw-2"}], "total_count": 3, "limit": 2},
        {"items": [{"id": "fw-3"}], "total_count": 3, "limit": 2},
    ]

    assert get(api_session, "https://app.example.com") == [
        {"id": "fw-1"},
        {"id": "fw-2"},
        {"id": "fw-3"},
    ]
    assert api_session.get.call_count == 2
