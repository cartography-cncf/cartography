"""
In-memory Airbyte public API served through a requests transport adapter, so
tests run the real AirbyteClient (token exchange, pagination, raise_for_status,
JSON decoding) against synthetic provider responses.
"""

import json
from typing import Any
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

import requests
from requests.adapters import BaseAdapter

from cartography.intel.airbyte.util import AirbyteClient
from tests.data.airbyte import multi_org

# Airbyte returns RFC 7807 problem documents for authorization failures.
FORBIDDEN_DETAIL = "Caller does not have the required permissions (synthetic)."
FORBIDDEN_BODY = {
    "type": "https://reference.airbyte.com/reference/errors",
    "title": "forbidden",
    "status": 403,
    "detail": FORBIDDEN_DETAIL,
}
TEST_CLIENT_ID = "synthetic-client-id"
TEST_CLIENT_SECRET = "synthetic-client-secret"
TEST_ACCESS_TOKEN = "synthetic-access-token"


class FakeAirbyteAPI(BaseAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.permissions = multi_org.initial_permissions()
        # Set to paginate GET /users; the real endpoint returns a single page.
        self.users_page_size: int | None = None
        # The user that owns the application, whose own permissions Airbyte
        # returns in full.
        self.owner = multi_org.APP_OWNER
        self._failures: list[tuple[str, str, dict[str, str], Any]] = []
        self.requests: list[tuple[str, str, dict[str, str]]] = []

    def fail(self, method: str, uri: str, result: Any, **params: str) -> None:
        """
        Answer matching requests with ``result``: an HTTP status code, a
        ``(status, body)`` tuple, or an exception to raise from the transport.
        ``params`` must all match the request's query parameters.
        """
        self._failures.append((method, uri, params, result))

    def clear_failures(self) -> None:
        self._failures = []

    def send(self, request, **kwargs):
        url = urlsplit(request.url)
        uri = url.path.removeprefix(urlsplit(multi_org.API_URL).path)
        params = dict(parse_qsl(url.query))
        self.requests.append((request.method, uri, params))

        for method, failing_uri, failing_params, result in self._failures:
            if (method, failing_uri) != (request.method, uri):
                continue
            if any(params.get(k) != v for k, v in failing_params.items()):
                continue
            if isinstance(result, Exception):
                raise result
            if isinstance(result, tuple):
                return _response(request, *result)
            return _response(request, result, FORBIDDEN_BODY)

        if (request.method, uri) == ("POST", "/applications/token"):
            return _response(
                request,
                200,
                {
                    "access_token": TEST_ACCESS_TOKEN,
                    "token_type": "Bearer",
                    "expires_in": 900,
                },
            )
        if request.method != "GET":
            return _response(request, 405, {"status": 405})
        handler = {
            "/organizations": self._organizations,
            "/workspaces": self._workspaces,
            "/users": self._users,
            "/permissions": self._permissions,
            "/sources": self._sources,
            "/destinations": self._empty,
            "/tags": self._empty,
            "/connections": self._empty,
        }.get(uri)
        if handler is None:
            return _response(request, 404, {"status": 404})
        return _response(request, 200, handler(params))

    def close(self) -> None:
        pass

    def _organizations(self, params: dict[str, str]) -> dict:
        return {"data": multi_org.ORGANIZATIONS}

    def _workspaces(self, params: dict[str, str]) -> dict:
        return {"data": multi_org.WORKSPACES}

    def _sources(self, params: dict[str, str]) -> dict:
        workspace_ids = params["workspaceIds"].split(",")
        return {
            "data": [s for s in multi_org.SOURCES if s["workspaceId"] in workspace_ids],
        }

    def _empty(self, params: dict[str, str]) -> dict:
        return {"data": []}

    def _users(self, params: dict[str, str]) -> dict:
        org_permissions = self.permissions[params["organizationId"]]
        user_ids = sorted({p["userId"] for p in org_permissions})
        users = [multi_org.USERS[user_id] for user_id in user_ids]
        if self.users_page_size is None:
            return {"data": users}
        offset = int(params.get("offset", 0))
        page = users[offset : offset + self.users_page_size]
        more = offset + self.users_page_size < len(users)
        return {"data": page, "next": "next-page" if more else ""}

    def _permissions(self, params: dict[str, str]) -> dict:
        user_id = params.get("userId", self.owner)
        if user_id == self.owner:
            # Reading your own permissions ignores organizationId.
            return {
                "data": [
                    p
                    for org_permissions in self.permissions.values()
                    for p in org_permissions
                    if p["userId"] == user_id
                ],
            }
        # Another user's permissions in an organization are its organization
        # roles only; Airbyte filters out workspace permissions.
        return {
            "data": [
                p
                for p in self.permissions[params["organizationId"]]
                if p["userId"] == user_id and p["scope"] == "organization"
            ],
        }


def _response(
    request: requests.PreparedRequest,
    status: int,
    body: Any,
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.reason = {200: "OK", 403: "Forbidden"}.get(status, "Error")
    response._content = body if isinstance(body, bytes) else json.dumps(body).encode()
    response.headers["Content-Type"] = (
        "application/json" if status < 400 else "application/problem+json"
    )
    response.url = request.url or ""
    response.request = request
    return response


def make_client(api: FakeAirbyteAPI) -> AirbyteClient:
    client = AirbyteClient(multi_org.API_URL, TEST_CLIENT_ID, TEST_CLIENT_SECRET)
    client._session.mount(multi_org.API_URL, api)
    return client
