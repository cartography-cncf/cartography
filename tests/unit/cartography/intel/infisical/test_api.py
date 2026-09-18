from unittest.mock import MagicMock

import pytest
import requests

import cartography.intel.infisical
from cartography.intel.infisical import api
from tests.data.infisical import API_URL
from tests.data.infisical import ORGANIZATION_ID
from tests.data.infisical import PROJECTS


@pytest.mark.parametrize(
    ("organization_id", "client_id", "client_secret"),
    [
        (None, "client-id", "client-secret"),
        ("org-123", None, "client-secret"),
        ("org-123", "client-id", None),
    ],
)  # type: ignore[misc]
def test_start_infisical_ingestion_skips_incomplete_config(
    mocker,
    organization_id: str | None,
    client_id: str | None,
    client_secret: str | None,
) -> None:
    # Arrange
    config = MagicMock(
        infisical_api_url=API_URL,
        infisical_organization_id=organization_id,
        infisical_client_id=client_id,
        infisical_client_secret=client_secret,
    )
    create_session = mocker.patch.object(api, "create_session")

    # Act
    cartography.intel.infisical.start_infisical_ingestion(MagicMock(), config)

    # Assert
    create_session.assert_not_called()


def test_normalize_api_url_accepts_origin_and_trailing_slash() -> None:
    # Act and assert
    assert api.normalize_api_url(f"{API_URL}/") == API_URL


@pytest.mark.parametrize(
    "api_url",
    [
        "app.infisical.example",
        "ftp://app.infisical.example",
        "https://user:password@app.infisical.example",
        "https://app.infisical.example/api",
        "https://app.infisical.example?tenant=1",
        "https://app.infisical.example#fragment",
    ],
)  # type: ignore[misc]
def test_normalize_api_url_rejects_non_origins(api_url: str) -> None:
    # Act and assert
    with pytest.raises(ValueError, match="Infisical API URL"):
        api.normalize_api_url(api_url)


def test_create_session_uses_universal_auth(mocker) -> None:
    # Arrange
    response = MagicMock()
    response.json.return_value = {"accessToken": " access-token "}
    post = mocker.patch.object(requests, "post", return_value=response)

    # Act
    session = api.create_session(API_URL, "client-id", "client-secret")

    # Assert
    post.assert_called_once_with(
        f"{API_URL}/api/v1/auth/universal-auth/login",
        json={"clientId": "client-id", "clientSecret": "client-secret"},
        timeout=(10, 60),
    )
    response.raise_for_status.assert_called_once_with()
    assert session.headers["Authorization"] == "Bearer access-token"
    assert session.headers["User-Agent"] == "cartography-infisical"
    session.close()


def test_get_projects_uses_organization_endpoint() -> None:
    # Arrange
    response = MagicMock()
    response.json.return_value = {"workspaces": PROJECTS}
    session = MagicMock(spec=requests.Session)
    session.get.return_value = response

    # Act
    projects = api.get_projects(session, API_URL, ORGANIZATION_ID)

    # Assert
    assert projects == PROJECTS
    session.get.assert_called_once_with(
        f"{API_URL}/api/v2/organizations/{ORGANIZATION_ID}/workspaces",
        timeout=(10, 60),
    )
    response.raise_for_status.assert_called_once_with()


@pytest.mark.parametrize(
    "payload",
    [None, [], {}, {"workspaces": None}, {"workspaces": ["not-an-object"]}],
)  # type: ignore[misc]
def test_get_projects_rejects_invalid_responses(payload) -> None:
    # Arrange
    response = MagicMock()
    response.json.return_value = payload
    session = MagicMock(spec=requests.Session)
    session.get.return_value = response

    # Act and assert
    with pytest.raises((KeyError, RuntimeError)):
        api.get_projects(session, API_URL, ORGANIZATION_ID)
