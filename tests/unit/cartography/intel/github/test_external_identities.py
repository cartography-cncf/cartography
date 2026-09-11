import json
from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.github.external_identities import get_external_identities
from cartography.intel.github.external_identities import transform_external_identities
from tests.data.github.external_identities import API_URL
from tests.data.github.external_identities import FORBIDDEN
from tests.data.github.external_identities import IDENTITIES
from tests.data.github.external_identities import NO_SAML_PROVIDER
from tests.data.github.external_identities import ORG
from tests.data.github.external_identities import ORG_URL
from tests.data.github.external_identities import page


def test_transform_preserves_nameid_and_nullable_fields():
    # Arrange
    identities = deepcopy(IDENTITIES)
    identities[1]["samlIdentity"]["nameId"] = "opaque-id-123"

    # Act
    result = transform_external_identities(identities, ORG_URL)

    # Assert
    assert result == [
        {
            "id": f"{ORG_URL}|E_example_alice",
            "saml_name_id": " Alice@Example.com ",
            "user_url": "https://github.com/example-alice",
        },
        {
            "id": f"{ORG_URL}|E_example_bob",
            "saml_name_id": "opaque-id-123",
            "user_url": "https://github.com/example-bob",
        },
        {
            "id": f"{ORG_URL}|E_example_unlinked",
            "saml_name_id": "unlinked@example.com",
            "user_url": None,
        },
        {
            "id": f"{ORG_URL}|E_example_without_saml",
            "saml_name_id": None,
            "user_url": "https://github.com/example-carol",
        },
    ]
    assert identities[0] == IDENTITIES[0]
    assert (
        transform_external_identities(
            identities, "https://github.example.com/example-org"
        )[0]["id"]
        != result[0]["id"]
    )


@patch("cartography.intel.github.util.requests.post")
def test_get_paginates(mock_post):
    # Arrange
    mock_post.side_effect = [
        Mock(json=lambda: page(IDENTITIES[:2], has_next_page=True, cursor="cursor-1")),
        Mock(json=lambda: page(IDENTITIES[2:])),
    ]

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == (IDENTITIES, ORG_URL)
    assert [
        json.loads(call.kwargs["json"]["variables"])
        for call in mock_post.call_args_list
    ] == [
        {"login": ORG, "cursor": None},
        {"login": ORG, "cursor": "cursor-1"},
    ]


@pytest.mark.parametrize(
    "response,expected",
    [(NO_SAML_PROVIDER, None), (page([]), ([], ORG_URL)), (FORBIDDEN, None)],
)
@patch("cartography.intel.github.util.requests.post")
def test_get_distinguishes_absence_from_denied_access(mock_post, response, expected):
    # Arrange
    mock_post.return_value.json.return_value = response

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "error",
    [
        {"message": "timedout"},
        {"type": "RATE_LIMITED", "message": "API rate limit exceeded"},
    ],
)
@patch("cartography.intel.github.util.requests.post")
def test_get_rejects_partial_graphql_results(mock_post, error):
    # Arrange
    response = page(IDENTITIES)
    response["errors"] = [error]
    mock_post.return_value.json.return_value = response

    # Act and assert
    with pytest.raises(RuntimeError, match="query failed"):
        get_external_identities("test-token", API_URL, ORG)


@patch("cartography.intel.github.util.requests.post")
def test_get_propagates_http_failure(mock_post):
    # Arrange
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("401")

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_external_identities("test-token", API_URL, ORG)


@patch("cartography.intel.github.util.requests.post")
def test_get_rejects_nonadvancing_pagination(mock_post):
    # Arrange
    mock_post.return_value.json.return_value = page(
        IDENTITIES, has_next_page=True, cursor="same-cursor"
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="did not advance"):
        get_external_identities("test-token", API_URL, ORG)
    assert mock_post.call_count == 2
