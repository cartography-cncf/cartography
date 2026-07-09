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
