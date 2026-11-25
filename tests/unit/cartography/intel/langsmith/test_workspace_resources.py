from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.workspace_resources import get_mcp_servers
from cartography.intel.langsmith.workspace_resources import get_projects
from cartography.intel.langsmith.workspace_resources import get_taggings
from cartography.intel.langsmith.workspace_resources import transform_deployment_tags
from cartography.intel.langsmith.workspace_resources import transform_project_tags


def _http_error(status_code: int) -> requests.HTTPError:
    response = MagicMock()
    response.status_code = status_code
    return requests.HTTPError(f"{status_code} Client Error", response=response)


def _client(gateway_side_effect):
    client = MagicMock()
    client.get.return_value = {
        "mcp_vendors": [{"vendor_id": "arcade"}, {"vendor_id": "composio"}]
    }
    client.get_paginated_envelope.side_effect = gateway_side_effect
    return client


@pytest.mark.parametrize(
    "first_vendor_error, expected_complete",
    [
        # Registered but not OAuth-connected: it has no gateways, which is a full answer.
        (_http_error(400), True),
        # The vendor route is not served: also nothing to list.
        (LangSmithFetchError("/mcp-servers", 404, "HTTP 404"), True),
        # Hidden from this credential: gateways may exist, so cleanup must be skipped.
        (LangSmithFetchError("/mcp-servers", 403, "HTTP 403"), False),
    ],
)
def test_get_mcp_servers_skips_a_failing_vendor(first_vendor_error, expected_complete):
    # Arrange
    client = _client(
        [
            first_vendor_error,
            [{"id": "gw-1", "name": "Composio gateway", "tools": []}],
        ]
    )

    # Act
    servers, complete = get_mcp_servers(client, "org-1", "ws-1")

    # Assert
    assert [s["id"] for s in servers] == ["gw-1"]
    assert complete is expected_complete


def test_get_mcp_servers_reraises_other_http_errors():
    # Arrange
    client = _client([_http_error(500)])

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_mcp_servers(client, "org-1", "ws-1")


def test_get_taggings_indexes_tag_values_by_resource_type_and_id():
    # Arrange
    client = MagicMock()
    client.get.return_value = [
        {
            "tag_value_id": "tv-prod",
            "resources": {
                "projects": [{"resource_id": "proj-1"}],
                "deployments": [{"resource_id": "dep-1"}],
                "datasets": [],
            },
        },
        {
            "tag_value_id": "tv-team",
            "resources": {"projects": [{"resource_id": "proj-1"}]},
        },
    ]

    # Act
    taggings, complete = get_taggings(client, "org-1", "ws-1")

    # Assert
    assert taggings == {
        "projects": {"proj-1": ["tv-prod", "tv-team"]},
        "deployments": {"dep-1": ["tv-prod"]},
        "datasets": {},
    }
    assert complete is True


@pytest.mark.parametrize(
    "status, expected_complete",
    [(404, True), (403, False), (None, False)],
)
def test_get_taggings_reports_failures(status, expected_complete):
    # Arrange
    client = MagicMock()
    client.get.side_effect = LangSmithFetchError(
        "/api/v1/workspaces/current/taggings", status, "failed"
    )

    # Act
    taggings, complete = get_taggings(client, "org-1", "ws-1")

    # Assert
    assert taggings == {}
    assert complete is expected_complete


def test_transform_project_tags_emits_one_record_per_tag_value():
    # Act
    records = transform_project_tags({"proj-1": ["tv-prod", "tv-team"]})

    # Assert
    assert records == [
        {"project_id": "proj-1", "tag_value_id": "tv-prod"},
        {"project_id": "proj-1", "tag_value_id": "tv-team"},
    ]


def test_transform_deployment_tags_emits_one_record_per_tag_value():
    # Act
    records = transform_deployment_tags({"dep-1": ["tv-prod", "tv-team"]})

    # Assert
    assert records == [
        {"deployment_id": "dep-1", "tag_value_id": "tv-prod"},
        {"deployment_id": "dep-1", "tag_value_id": "tv-team"},
    ]


def test_get_projects_requests_tracing_projects_without_enrichment():
    # Arrange
    client = MagicMock()

    # Act
    get_projects(client, "org-1", "ws-1")

    # Assert
    client.get_paginated.assert_called_once_with(
        "/api/v1/sessions",
        params={"reference_free": "true", "skip_enrichment": "true"},
        org_id="org-1",
        tenant_id="ws-1",
        page_size=100,
    )
