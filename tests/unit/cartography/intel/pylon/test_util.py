from unittest.mock import MagicMock

import pytest

from cartography.intel.pylon.util import EU_BASE_URL
from cartography.intel.pylon.util import paginated_get
from cartography.intel.pylon.util import resolve_base_url
from cartography.intel.pylon.util import US_BASE_URL


@pytest.mark.parametrize(
    ("token", "base_url", "expected"),
    [
        ("pylon_api_abc", None, US_BASE_URL),
        ("pylon_api_eu_abc", None, EU_BASE_URL),
        ("legacy-token-without-prefix", None, US_BASE_URL),
        ("pylon_api_eu_abc", "https://pylon.example.com/", "https://pylon.example.com"),
    ],
)
def test_resolve_base_url(token, base_url, expected):
    # Act and assert
    assert resolve_base_url(token, base_url) == expected


def _response(body):
    response = MagicMock()
    response.json.return_value = body
    return response


def test_paginated_get_follows_cursor():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response(
            {
                "data": [{"id": "1"}],
                "pagination": {"cursor": "next", "has_next_page": True},
            },
        ),
        _response({"data": [{"id": "2"}], "pagination": {"has_next_page": False}}),
    ]

    # Act
    results = paginated_get(
        session, "https://api/users", {"include_deactivated": "true"}
    )

    # Assert
    assert results == [{"id": "1"}, {"id": "2"}]
    assert session.get.call_args_list[1].kwargs["params"] == {
        "include_deactivated": "true",
        "cursor": "next",
    }


def test_paginated_get_without_pagination_returns_single_page():
    # Arrange
    session = MagicMock()
    session.get.return_value = _response({"data": [{"id": "1"}]})

    # Act
    results = paginated_get(session, "https://api/teams")

    # Assert
    assert results == [{"id": "1"}]


@pytest.mark.parametrize("cursor", [None, "same"])
def test_paginated_get_rejects_a_missing_or_repeated_cursor(cursor):
    # Arrange
    session = MagicMock()
    session.get.return_value = _response(
        {"data": [], "pagination": {"cursor": cursor, "has_next_page": True}},
    )

    # Act and assert
    with pytest.raises(ValueError):
        paginated_get(session, "https://api/teams")
