from unittest.mock import MagicMock

from cartography.intel.subimage.apikeys import get


def test_get_reads_page_envelope():
    # Regression: GET /api/api-keys/subimage returns the Page[T] envelope
    # ({"items": [...]}); get() must unwrap it, not iterate the dict keys.
    api_session = MagicMock()
    api_session.get.return_value.json.return_value = {
        "items": [{"app_id": "app-1"}],
        "total_count": 1,
        "limit": 100,
        "offset": 0,
    }

    assert get(api_session, "https://app.example.com") == [{"app_id": "app-1"}]


def test_get_paginates_all_pages():
    # Regression: get() must walk every page, not just the first, or cleanup
    # would delete API keys living on later pages.
    api_session = MagicMock()
    api_session.get.return_value.json.side_effect = [
        {
            "items": [{"app_id": "app-1"}, {"app_id": "app-2"}],
            "total_count": 3,
            "limit": 2,
        },
        {"items": [{"app_id": "app-3"}], "total_count": 3, "limit": 2},
    ]

    assert get(api_session, "https://app.example.com") == [
        {"app_id": "app-1"},
        {"app_id": "app-2"},
        {"app_id": "app-3"},
    ]
    assert api_session.get.call_count == 2
