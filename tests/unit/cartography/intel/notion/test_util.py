import base64
import json
from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.notion.util import create_api_session
from cartography.intel.notion.util import create_scim_session
from cartography.intel.notion.util import get_paginated
from cartography.intel.notion.util import get_scim_paginated
from cartography.intel.notion.util import NOTION_API_VERSION
from cartography.intel.notion.util import parse_config


def _encode(value):
    return base64.b64encode(json.dumps(value).encode()).decode()


def test_parse_config_accepts_multiple_workspaces():
    # Arrange
    encoded = _encode(
        {
            "workspaces": [
                {
                    "workspace_id": "ws-1",
                    "workspace_name": "One",
                    "api_token": "ntn_one",
                },
                {
                    "workspace_id": "ws-2",
                    "workspace_name": "Two",
                    "api_token": "ntn_two",
                },
            ],
        },
    )

    # Act
    workspaces = parse_config(encoded)

    # Assert
    assert [workspace.workspace_id for workspace in workspaces] == ["ws-1", "ws-2"]


def test_parse_config_accepts_optional_scim_token():
    # Arrange
    encoded = _encode(
        {
            "workspaces": [
                {
                    "workspace_id": "ws-1",
                    "workspace_name": "One",
                    "api_token": "ntn_one",
                    "scim_token": "scim_one",
                },
            ],
        },
    )

    # Act and assert
    assert parse_config(encoded)[0].scim_token == "scim_one"


@pytest.mark.parametrize(
    "encoded",
    [
        "not-base64",
        _encode([]),
        _encode({}),
        _encode({"workspaces": []}),
        _encode({"workspaces": [{"workspace_id": "ws-1"}]}),
        _encode(
            {
                "workspaces": [
                    {
                        "workspace_id": "ws-1",
                        "workspace_name": "One",
                        "api_token": "ntn_one",
                        "scim_token": "",
                    },
                ],
            },
        ),
        _encode(
            {
                "workspaces": [
                    {
                        "workspace_id": "ws-1",
                        "workspace_name": "One",
                        "api_token": "ntn_one",
                    },
                    {
                        "workspace_id": "ws-1",
                        "workspace_name": "Duplicate",
                        "api_token": "ntn_two",
                    },
                ],
            },
        ),
    ],
)
def test_parse_config_rejects_invalid_config(encoded):
    # Act and assert
    with pytest.raises(ValueError):
        parse_config(encoded)


def _response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_create_api_session_configures_version_and_bounded_get_retries():
    # Act
    session = create_api_session("secret-token")

    # Assert
    retries = session.adapters["https://"].max_retries
    assert session.headers["Authorization"] == "Bearer secret-token"
    assert session.headers["Notion-Version"] == NOTION_API_VERSION
    assert retries.total == 5
    assert retries.allowed_methods == frozenset({"GET"})
    assert retries.respect_retry_after_header is True
    session.close()


def test_create_scim_session_uses_scim_media_type_and_same_retry_policy():
    # Act
    session = create_scim_session("scim-token")

    # Assert
    assert session.headers["Authorization"] == "Bearer scim-token"
    assert session.headers["Accept"] == "application/scim+json"
    assert session.adapters["https://"].max_retries.total == 5
    session.close()


def test_get_paginated_reads_every_page():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response({"results": [{"id": "one"}], "has_more": True, "next_cursor": "c2"}),
        _response({"results": [{"id": "two"}], "has_more": False, "next_cursor": None}),
    ]

    # Act
    result = get_paginated(session, "users")

    # Assert
    assert result == [{"id": "one"}, {"id": "two"}]
    assert session.get.call_args_list[1].kwargs["params"]["start_cursor"] == "c2"


@pytest.mark.parametrize(
    "payloads",
    [
        [[{"id": "not-an-object"}]],
        [{"results": {}, "has_more": False}],
        [{"results": [], "has_more": "false"}],
        [{"results": [], "has_more": True, "next_cursor": None}],
        [
            {"results": [], "has_more": True, "next_cursor": "same"},
            {"results": [], "has_more": True, "next_cursor": "same"},
        ],
    ],
)
def test_get_paginated_rejects_malformed_or_nonprogressing_responses(payloads):
    # Arrange
    session = MagicMock()
    session.get.side_effect = [_response(payload) for payload in payloads]

    # Act and assert
    with pytest.raises(ValueError):
        get_paginated(session, "users")


def test_get_scim_paginated_reads_every_page():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response(
            {
                "Resources": [{"id": "one"}],
                "totalResults": 2,
                "startIndex": 1,
                "itemsPerPage": 1,
            },
        ),
        _response(
            {
                "Resources": [{"id": "two"}],
                "totalResults": 2,
                "startIndex": 2,
                "itemsPerPage": 1,
            },
        ),
    ]

    # Act
    result = get_scim_paginated(session, "Users")

    # Assert
    assert result == [{"id": "one"}, {"id": "two"}]
    assert session.get.call_args_list[1].kwargs["params"] == {
        "startIndex": 2,
        "count": 100,
    }


def test_get_scim_paginated_propagates_authentication_failure():
    # Arrange
    session = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
    session.get.return_value = response

    # Act and assert
    with pytest.raises(requests.HTTPError, match="401 Unauthorized"):
        get_scim_paginated(session, "Users")


@pytest.mark.parametrize(
    "payloads",
    [
        [[{"id": "not-an-object"}]],
        [{"Resources": {}, "totalResults": 0, "startIndex": 1, "itemsPerPage": 0}],
        [{"Resources": [], "totalResults": True, "startIndex": 1, "itemsPerPage": 0}],
        [{"Resources": [], "totalResults": 1, "startIndex": 1, "itemsPerPage": 0}],
        [
            {
                "Resources": [{"id": "one"}],
                "totalResults": 2,
                "startIndex": 1,
                "itemsPerPage": 1,
            },
            {
                "Resources": [{"id": "two"}],
                "totalResults": 3,
                "startIndex": 2,
                "itemsPerPage": 1,
            },
        ],
    ],
)
def test_get_scim_paginated_rejects_malformed_or_nonprogressing_responses(payloads):
    # Arrange
    session = MagicMock()
    session.get.side_effect = [_response(payload) for payload in payloads]

    # Act and assert
    with pytest.raises(ValueError):
        get_scim_paginated(session, "Users")
