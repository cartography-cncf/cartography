from unittest.mock import Mock

import pytest

from cartography.intel.render.envgroups import get
from cartography.intel.render.envgroups import transform


def _response(body):
    mock_response = Mock()
    mock_response.json.return_value = body
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_get_parses_render_s_undocumented_bare_array_env_groups_response():
    """
    Render's OpenAPI spec documents GET /env-groups as returning a bare array of
    envGroupMeta objects - not the {"envGroup": {...}, "cursor": ...} wrapper used by
    most other list endpoints (confirmed against
    https://api-docs.render.com/v1.0/openapi/render-public-api-1.json, and matching
    the same bare-array shape already handled for /registrycredentials and
    /dedicated-ips). get() must unwrap this shape directly rather than routing it
    through list_paginated(), which would raise on every real, non-empty response.
    """
    session = Mock()
    session.get.return_value = _response(
        [{"id": "evg-1", "name": "shared", "ownerId": "tea-1"}],
    )

    groups = get(session, "tea-1")

    assert groups == [{"id": "evg-1", "name": "shared", "ownerId": "tea-1"}]


def test_transform_emits_one_row_per_linked_service():
    groups = [
        {
            "id": "evg-1",
            "name": "shared",
            "ownerId": "tea-1",
            "serviceLinks": [{"id": "srv-1"}, {"id": "srv-2"}],
        },
    ]

    rows = transform(groups)

    assert {row["service_id"] for row in rows} == {"srv-1", "srv-2"}
    assert all(row["id"] == "evg-1" for row in rows)


def test_transform_emits_a_row_with_no_service_id_when_unlinked():
    groups = [{"id": "evg-1", "name": "unlinked", "serviceLinks": []}]

    rows = transform(groups)

    assert rows == [
        {
            "id": "evg-1",
            "name": "unlinked",
            "ownerId": None,
            "environmentId": None,
            "createdAt": None,
            "updatedAt": None,
            "service_id": None,
        }
    ]


def test_transform_raises_on_service_link_missing_an_id():
    """
    A serviceLinks entry present but missing its id must fail loudly rather than
    silently produce a row with service_id=None, which would drop the LINKED_TO edge
    with no error signal - inconsistent with this module's raise-on-malformed pattern.
    """
    groups = [
        {
            "id": "evg-1",
            "name": "shared",
            "serviceLinks": [{"name": "no-id-here", "type": "web"}],
        },
    ]

    with pytest.raises(ValueError):
        transform(groups)
