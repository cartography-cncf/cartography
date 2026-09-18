from typing import Any
from urllib.parse import urlparse

import requests

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 60
REQUEST_TIMEOUT = (CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)
UNIVERSAL_AUTH_LOGIN_PATH = "/api/v1/auth/universal-auth/login"
ORGANIZATION_PROJECTS_PATH = "/api/v2/organizations/{organization_id}/workspaces"


def normalize_api_url(api_url: str) -> str:
    """Validate and normalize an Infisical API origin."""
    parsed = urlparse(api_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Infisical API URL must be an absolute HTTP(S) origin")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Infisical API URL must not contain user information")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Infisical API URL contains an invalid port") from exc
    if parsed.path.rstrip("/") or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(
            "Infisical API URL must be an origin without a route, query, or fragment",
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def create_session(
    api_url: str,
    client_id: str,
    client_secret: str,
) -> requests.Session:
    """Exchange Universal Auth credentials for an authenticated API session."""
    endpoint = normalize_api_url(api_url)
    response = requests.post(
        f"{endpoint}{UNIVERSAL_AUTH_LOGIN_PATH}",
        json={"clientId": client_id, "clientSecret": client_secret},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Infisical Universal Auth returned a non-object response")
    access_token = payload["accessToken"]
    if not isinstance(access_token, str) or not access_token.strip():
        raise RuntimeError("Infisical Universal Auth returned an invalid access token")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {access_token.strip()}",
            "Accept": "application/json",
            "User-Agent": "cartography-infisical",
        },
    )
    return session


def get_projects(
    session: requests.Session,
    api_url: str,
    organization_id: str,
) -> list[dict[str, Any]]:
    """Return projects visible to the configured Infisical machine identity."""
    endpoint = normalize_api_url(api_url)
    path = ORGANIZATION_PROJECTS_PATH.format(organization_id=organization_id)
    response = session.get(f"{endpoint}{path}", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Infisical projects API returned a non-object response")
    projects = payload["workspaces"]
    if not isinstance(projects, list) or any(
        not isinstance(project, dict) for project in projects
    ):
        raise RuntimeError("Infisical projects API returned an invalid workspaces list")
    return projects
