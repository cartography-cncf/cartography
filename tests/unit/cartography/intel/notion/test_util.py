import base64
import json
from unittest.mock import MagicMock

import pytest

from cartography.intel.notion.util import create_api_session
from cartography.intel.notion.util import get_paginated
from cartography.intel.notion.util import NOTION_API_VERSION
from cartography.intel.notion.util import parse_config
from cartography.intel.notion.util import post_paginated


def _encode(value):
    return base64.b64encode(json.dumps(value).encode()).decode()


def test_parse_config_accepts_multiple_workspaces():
    # Arrange
    encoded = _encode(
        {
            "workspaces": [
                {
                    "api_token": "ntn_one",
                    "sync_public_pages": True,
                },
                {
                    "api_token": "ntn_two",
                },
            ],
        },
    )

    # Act
    workspaces = parse_config(encoded)

    # Assert
    assert [workspace.api_token for workspace in workspaces] == ["ntn_one", "ntn_two"]
    assert [workspace.sync_public_pages for workspace in workspaces] == [True, False]


@pytest.mark.parametrize(
    "encoded",
    [
        "not-base64",
        _encode([]),
        _encode({}),
        _encode({"workspaces": []}),
        _encode({"workspaces": [{"sync_public_pages": True}]}),
        _encode(
            {
                "workspaces": [
                    {"api_token": "ntn_one", "sync_public_pages": "yes"},
                ],
            },
        ),
        _encode(
            {
                "workspaces": [
                    {"api_token": "ntn_one"},
                    {"api_token": "ntn_one"},
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


def _list_payload(result_type, results, has_more=False, next_cursor=None):
    return {
        "object": "list",
        "type": result_type,
        result_type: {},
        "results": results,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def test_create_api_session_configures_version_and_bounded_read_retries():
    # Act
    session = create_api_session("secret-token")

    # Assert
    retries = session.adapters["https://"].max_retries
    assert session.headers["Authorization"] == "Bearer secret-token"
    assert session.headers["Notion-Version"] == NOTION_API_VERSION
    assert retries.total == 5
    assert retries.allowed_methods == frozenset({"GET", "POST"})
    assert retries.respect_retry_after_header is True
    session.close()


def test_get_paginated_reads_every_page():
    # Arrange
    session = MagicMock()
    session.get.side_effect = [
        _response(_list_payload("user", [{"id": "one"}], True, "c2")),
        _response(_list_payload("user", [{"id": "two"}])),
    ]

    # Act
    result = get_paginated(session, "users", "user")

    # Assert
    assert result == [{"id": "one"}, {"id": "two"}]
    assert session.get.call_args_list[1].kwargs["params"]["start_cursor"] == "c2"


def test_post_paginated_reads_every_page_without_mutating_body():
    # Arrange
    session = MagicMock()
    session.post.side_effect = [
        _response(_list_payload("page_or_data_source", [{"id": "one"}], True, "c2")),
        _response(_list_payload("page_or_data_source", [{"id": "two"}])),
    ]
    body = {"filter": {"property": "object", "value": "page"}}

    # Act
    result = list(post_paginated(session, "search", body, "page_or_data_source"))

    # Assert
    assert result == [[{"id": "one"}], [{"id": "two"}]]
    assert body == {"filter": {"property": "object", "value": "page"}}
    assert session.post.call_args_list[1].kwargs["json"]["start_cursor"] == "c2"


@pytest.mark.parametrize(
    "payloads",
    [
        [[{"id": "not-an-object"}]],
        [{"results": {}, "has_more": False}],
        [_list_payload("user", {}, False)],
        [_list_payload("user", [], "false")],
        [_list_payload("user", [], True, None)],
        [
            _list_payload("user", [], True, "same"),
            _list_payload("user", [], True, "same"),
        ],
    ],
)
def test_get_paginated_rejects_malformed_or_nonprogressing_responses(payloads):
    # Arrange
    session = MagicMock()
    session.get.side_effect = [_response(payload) for payload in payloads]

    # Act and assert
    with pytest.raises(ValueError):
        get_paginated(session, "users", "user")


@pytest.mark.parametrize(
    "payloads",
    [
        [[{"id": "not-an-object"}]],
        [{"results": {}, "has_more": False}],
        [_list_payload("page_or_data_source", {}, False)],
        [_list_payload("page_or_data_source", [], "false")],
        [_list_payload("page_or_data_source", [], True, None)],
        [
            _list_payload("page_or_data_source", [], True, "same"),
            _list_payload("page_or_data_source", [], True, "same"),
        ],
    ],
)
def test_post_paginated_rejects_malformed_or_nonprogressing_responses(payloads):
    # Arrange
    session = MagicMock()
    session.post.side_effect = [_response(payload) for payload in payloads]

    # Act and assert
    with pytest.raises(ValueError):
        list(post_paginated(session, "search", {}, "page_or_data_source"))
