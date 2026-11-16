import pytest

from cartography.intel.sentra import api

PATH = "/api/core/data-stores/search"


def test_iter_search_pages_follows_keyset_cursor_until_short_page(mocker):
    # Arrange
    rows = [{"id": f"store-{i}"} for i in range(5)]
    requests_seen = []

    def post_search(_session, _api_url, _path, body):
        requests_seen.append(dict(body))
        cursor = body.get("start_from_id")
        remaining = [r for r in rows if cursor is None or r["id"] > cursor]
        return {"items": remaining[: body["limit"]]}

    mocker.patch.object(api, "post_search", side_effect=post_search)

    # Act
    pages = list(
        api.iter_search_pages(
            None,
            "https://app.sentra.io",
            PATH,
            filters={"region": {"op": "EQ", "values": ["us-east-1"]}},
            page_size=2,
        ),
    )

    # Assert
    assert pages == [rows[0:2], rows[2:4], rows[4:5]]
    assert [body.get("start_from_id") for body in requests_seen] == [
        None,
        "store-1",
        "store-3",
    ]
    assert all(
        body["filters"] == {"region": {"op": "EQ", "values": ["us-east-1"]}}
        for body in requests_seen
    )


def test_iter_search_pages_stops_after_exactly_full_last_page(mocker):
    # Arrange
    rows = [{"id": "a"}, {"id": "b"}]

    def post_search(_session, _api_url, _path, body):
        cursor = body.get("start_from_id")
        return {"items": [r for r in rows if cursor is None or r["id"] > cursor]}

    mocker.patch.object(api, "post_search", side_effect=post_search)

    # Act
    pages = list(
        api.iter_search_pages(None, "https://app.sentra.io", PATH, page_size=2)
    )

    # Assert
    assert pages == [rows, []]


def test_iter_search_pages_raises_on_repeated_cursor(mocker):
    # Arrange
    mocker.patch.object(
        api,
        "post_search",
        return_value={"items": [{"id": "a"}, {"id": "b"}]},
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="repeated pagination cursor b"):
        list(api.iter_search_pages(None, "https://app.sentra.io", PATH, page_size=2))
