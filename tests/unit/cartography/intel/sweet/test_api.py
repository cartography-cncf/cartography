from unittest.mock import MagicMock

import pytest

from cartography.intel.sweet import api


def _response(body, next_keyset=None):
    response = MagicMock()
    response.json.return_value = body
    response.headers = {"x-sweet-next-keyset": next_keyset} if next_keyset else {}
    return response


def test_iter_pages_follows_keyset_header_one_page_at_a_time():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response([{"id": "1"}, {"id": "2"}], next_keyset="page-2"),
        _response([{"id": "3"}]),
    ]

    # Act
    pages = api.iter_pages(
        session,
        "https://eapi.sweet.security",
        "/v1/vulnerability",
        {"status": "open"},
        "vulnerabilities",
    )
    first_page = next(pages)
    calls_before_second_page = session.get.call_count

    # Assert
    assert calls_before_second_page == 1
    assert [first_page, *pages] == [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    assert session.get.call_args_list[1].kwargs["params"] == {
        "status": "open",
        "limit": 200,
        "keyset": "page-2",
    }


def test_iter_pages_raises_when_keyset_repeats():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response([{"id": "1"}], next_keyset="page-2"),
        _response([{"id": "2"}], next_keyset="page-2"),
    ]

    # Act and assert
    with pytest.raises(RuntimeError, match="repeated pagination keyset"):
        list(
            api.iter_pages(
                session,
                "https://eapi.sweet.security",
                "/v1/attack",
                {},
                "attack chains",
            ),
        )


def test_iter_pages_raises_on_non_list_response():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"message": "unexpected"})

    # Act and assert
    with pytest.raises(RuntimeError, match="non-list response"):
        list(
            api.iter_pages(
                session,
                "https://eapi.sweet.security",
                "/v1/attack",
                {},
                "attack chains",
            ),
        )


def test_normalize_api_url_strips_trailing_slash():
    assert (
        api.normalize_api_url("https://eapi.sweet.security/")
        == "https://eapi.sweet.security"
    )


@pytest.mark.parametrize(
    "api_url",
    [
        "http://eapi.sweet.security",
        "https://eapi.sweet.security/v1",
        "https://user:pass@eapi.sweet.security",
        "https://eapi.sweet.security:abc",
        "https://eapi.sweet.security:99999",
        "eapi.sweet.security",
    ],
)
def test_normalize_api_url_rejects_non_origin_urls(api_url):
    with pytest.raises(ValueError):
        api.normalize_api_url(api_url)
