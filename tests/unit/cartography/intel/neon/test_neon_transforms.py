from typing import Any

import pytest

from cartography.intel.neon.databases import transform_roles
from cartography.intel.neon.endpoints import endpoint_exposure
from cartography.intel.neon.projects import get as get_projects
from cartography.intel.neon.storage import transform_buckets
from cartography.intel.neon.storage import transform_credentials
from cartography.intel.neon.util import get_paginated


def _project(ips=None, protected_only=None, block_public=None) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    if ips is not None or protected_only is not None:
        settings["allowed_ips"] = {
            "ips": ips or [],
            "protected_branches_only": protected_only,
        }
    if block_public is not None:
        settings["block_public_connections"] = block_public
    return {"settings": settings}


@pytest.mark.parametrize(
    "project, endpoint, branch_protected, expected",
    [
        # No allowlist: open to the internet.
        (_project(), {}, False, True),
        # An allowlist applies to every branch.
        (_project(ips=["203.0.113.0/24"]), {}, False, False),
        # protected_branches_only leaves unprotected branches open...
        (_project(ips=["203.0.113.0/24"], protected_only=True), {}, False, True),
        # ...and restricts protected ones.
        (_project(ips=["203.0.113.0/24"], protected_only=True), {}, True, False),
        # An allowlist that admits every address is no restriction at all.
        (_project(ips=["0.0.0.0/0"]), {}, True, True),
        (_project(ips=["203.0.113.4", "::/0"]), {}, True, True),
        # An empty allowlist is the same as none.
        (_project(ips=[]), {}, True, True),
        # Blocking public connections closes everything.
        (_project(block_public=True), {}, False, False),
        # A disabled compute refuses every connection.
        (_project(), {"disabled": True}, False, False),
    ],
)
def test_endpoint_exposure(project, endpoint, branch_protected, expected):
    result = endpoint_exposure(endpoint, project, branch_protected)
    assert result["exposed_internet"] is expected
    assert result["exposed_internet_type"] == (["direct"] if expected else None)


def test_transform_roles_drops_password():
    roles = transform_roles(
        [
            {
                "branch_id": "br-a",
                "name": "app",
                "password": "npg_secret",
                "protected": False,
                "authentication_method": "password",
                "created_at": "2026-11-05T10:25:24Z",
                "updated_at": "2026-11-05T10:25:24Z",
            },
        ],
    )
    assert roles[0]["id"] == "br-a/app"
    assert "password" not in roles[0]
    assert "npg_secret" not in repr(roles)


def test_transform_credentials_keeps_only_metadata():
    credentials = transform_credentials(
        [
            {
                "token_id": "nak_live_x",
                "token_id_short": "x",
                "scopes": ["storage:read", "storage:write"],
                "principal_type": "user",
                "created_at": "2026-11-05T10:25:24Z",
                # Fields a credential *create* or *reveal* returns. A listing
                # never should, but if one did they must not be stored.
                "api_token": "napi_secret",
                "s3_secret_access_key": "s3_secret",
            },
        ],
        listed_on_branch_id="br-child",
    )
    assert credentials[0]["can_write_storage"] is True
    # No branch_id in the payload: fall back to the branch it was listed on.
    assert credentials[0]["branch_id"] == "br-child"
    assert "napi_secret" not in repr(credentials)
    assert "s3_secret" not in repr(credentials)


def test_transform_buckets_without_storage_endpoint():
    buckets = transform_buckets(
        [{"name": "b", "access_level": "public_read"}],
        "br-a",
        {},
    )
    assert buckets[0]["public"] is True
    assert buckets[0]["url"] is None


class _Response:
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class _Session:
    def __init__(self, pages: list[_Response]) -> None:
        self.pages = pages
        self.params: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.params.append(dict(params or {}))
        return self.pages.pop(0)


def test_get_paginated_follows_next_past_short_pages():
    session = _Session(
        [
            _Response(200, {"members": [{"id": 1}], "pagination": {"next": "c2"}}),
            _Response(200, {"members": [{"id": 2}], "pagination": {"next": "c3"}}),
            _Response(200, {"members": [], "pagination": {"next": "c4"}}),
        ],
    )
    items = get_paginated(session, "https://x/members", "members", 500)
    assert [i["id"] for i in items] == [1, 2]
    assert [p.get("cursor") for p in session.params] == [None, "c2", "c3"]


def test_get_paginated_tolerated_first_page_returns_none():
    session = _Session([_Response(403, {})])
    assert get_paginated(session, "https://x", "members", 10, tolerate=(403,)) is None


def test_get_paginated_tolerated_later_page_raises():
    session = _Session(
        [
            _Response(200, {"members": [{"id": 1}], "pagination": {"next": "c2"}}),
            _Response(403, {}),
        ],
    )
    with pytest.raises(RuntimeError):
        get_paginated(session, "https://x", "members", 10, tolerate=(403,))


def test_get_projects_reports_incomplete_listing():
    session = _Session(
        [
            _Response(
                200,
                {
                    "projects": [{"id": "p1"}],
                    "unavailable_project_ids": ["p2"],
                    "pagination": {"cursor": "p1"},
                },
            ),
        ],
    )
    projects, complete = get_projects(session, "https://x", "org-1")
    assert [p["id"] for p in projects] == ["p1"]
    assert complete is False
    assert session.params[0]["org_id"] == "org-1"
