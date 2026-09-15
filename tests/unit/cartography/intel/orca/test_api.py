from typing import cast
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

import cartography.intel.orca
from cartography.intel.orca import api


@pytest.mark.parametrize(
    ("api_endpoint", "api_token"),
    [
        (None, "test-token"),
        ("https://api.orcasecurity.example", None),
    ],
)  # type: ignore[misc]
def test_start_orca_ingestion_skips_incomplete_config(
    mocker,
    api_endpoint: str | None,
    api_token: str | None,
) -> None:
    # Arrange
    config = MagicMock(orca_api_endpoint=api_endpoint, orca_api_token=api_token)
    create_session = mocker.patch.object(api, "create_session")

    # Act
    cartography.intel.orca.start_orca_ingestion(MagicMock(), config)

    # Assert
    create_session.assert_not_called()


def test_start_orca_ingestion_skips_invalid_endpoint(mocker, caplog) -> None:
    # Arrange
    config = MagicMock(
        orca_api_endpoint="not-an-api-origin",
        orca_api_token="test-token",
    )
    create_session = mocker.patch.object(api, "create_session")

    # Act
    cartography.intel.orca.start_orca_ingestion(MagicMock(), config)

    # Assert
    create_session.assert_not_called()
    assert "Invalid Orca API endpoint" in caplog.text


def test_normalize_api_endpoint_accepts_origin_and_trailing_slash() -> None:
    # Act and assert
    assert (
        api.normalize_api_endpoint("https://api.orcasecurity.example/")
        == "https://api.orcasecurity.example"
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        "api.orcasecurity.example",
        "http://api.orcasecurity.example",
        "ftp://api.orcasecurity.example",
        "https://user:password@api.orcasecurity.example",
        "https://api.orcasecurity.example/api",
        "https://api.orcasecurity.example?tenant=1",
        "https://api.orcasecurity.example#fragment",
    ],
)  # type: ignore[misc]
def test_normalize_api_endpoint_rejects_non_origins(endpoint: str) -> None:
    # Act and assert
    with pytest.raises(ValueError, match="Orca API endpoint"):
        api.normalize_api_endpoint(endpoint)


def test_create_session_uses_token_auth_and_bounded_read_retries() -> None:
    # Act
    session = api.create_session("test-token")
    retry = cast(HTTPAdapter, session.get_adapter("https://")).max_retries

    # Assert
    assert session.headers["Authorization"] == "Token test-token"
    assert retry.total == 4
    assert retry.status_forcelist == api._RETRY_STATUS_CODES
    assert retry.allowed_methods == frozenset({"GET", "POST"})
    assert retry.respect_retry_after_header is True
    http_adapter = cast(HTTPAdapter, session.get_adapter("http://"))
    assert http_adapter.max_retries.total == 0
    session.close()


def test_get_organization_uses_identity_endpoint(mocker) -> None:
    # Arrange
    response = MagicMock()
    response.json.return_value = {
        "data": {
            "organization_id": " org-1 ",
            "organization_name": " Example ",
        },
    }
    session = MagicMock(spec=requests.Session)
    session.request.return_value = response

    # Act
    organization = api.get_organization(
        session,
        "https://api.orcasecurity.example/",
    )

    # Assert
    assert organization == {
        "id": "org-1",
        "name": "Example",
        "api_url": "https://api.orcasecurity.example",
    }
    session.request.assert_called_once_with(
        "GET",
        "https://api.orcasecurity.example/api/user/action",
        json=None,
        timeout=(10, 120),
    )
    response.raise_for_status.assert_called_once_with()


def test_get_organization_sanitizes_transport_errors() -> None:
    # Arrange
    session = MagicMock(spec=requests.Session)
    session.request.side_effect = requests.ConnectTimeout(
        "synthetic low-level transport details",
    )

    # Act and assert
    with pytest.raises(
        RuntimeError,
        match=r"^Orca GET /api/user/action request failed$",
    ) as exc_info:
        api.get_organization(session, "https://api.orcasecurity.example")

    assert "transport details" not in str(exc_info.value)


def test_iter_serving_layer_pages_advances_offset_and_count(mocker) -> None:
    # Arrange
    query = {"query": {"models": ["Alert"]}}
    query_call = mocker.patch(
        "cartography.intel.orca.api.serving_layer_query",
        side_effect=[
            {"data": [{"id": "1"}, {"id": "2"}], "total_items": 3},
            {"data": [{"id": "3"}]},
        ],
    )

    # Act
    pages = list(
        api.iter_serving_layer_pages(
            MagicMock(),
            "https://api.orcasecurity.example",
            query,
            page_size=2,
            result_name="alerts",
        ),
    )

    # Assert
    assert pages == [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    first_payload = query_call.call_args_list[0].args[2]
    second_payload = query_call.call_args_list[1].args[2]
    assert first_payload["start_at_index"] == 0
    assert first_payload["get_results_and_count"] is True
    assert second_payload["start_at_index"] == 2
    assert second_payload["get_results_and_count"] is False
    assert "limit" not in query


@pytest.mark.parametrize(
    ("responses", "message"),
    [
        ([{"data": []}], "omitted integer total_items"),
        (
            [
                {"data": [{"id": "1"}], "total_items": 2},
                {"data": []},
            ],
            "pagination stopped",
        ),
        (
            [
                {"data": [{"id": "1"}], "total_items": 2},
                {"data": [{"id": "1"}]},
            ],
            "repeated a page",
        ),
        ([{"data": [{"id": "1"}], "total_items": 0}], "more rows"),
    ],
)  # type: ignore[misc]
def test_iter_serving_layer_pages_rejects_incomplete_responses(
    mocker,
    responses: list[dict],
    message: str,
) -> None:
    # Arrange
    mocker.patch(
        "cartography.intel.orca.api.serving_layer_query",
        side_effect=responses,
    )

    # Act and assert
    with pytest.raises(RuntimeError, match=message):
        list(
            api.iter_serving_layer_pages(
                MagicMock(),
                "https://api.orcasecurity.example",
                {"query": {"models": ["Alert"]}},
                page_size=1,
                result_name="alerts",
            ),
        )


def test_iter_serving_layer_pages_rejects_excessive_page_count(mocker) -> None:
    # Arrange
    mocker.patch(
        "cartography.intel.orca.api.serving_layer_query",
        return_value={"data": [{"id": "1"}], "total_items": 11},
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="page safety limit"):
        list(
            api.iter_serving_layer_pages(
                MagicMock(),
                "https://api.orcasecurity.example",
                {"query": {"models": ["Alert"]}},
                page_size=1,
                result_name="alerts",
                max_pages=10,
            ),
        )
