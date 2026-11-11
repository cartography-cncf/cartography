import logging
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest
import requests

import cartography.intel.wiz.findings
import cartography.intel.wiz.issues
from cartography.intel.wiz.api import build_session
from cartography.intel.wiz.api import get_access_token
from cartography.intel.wiz.api import get_paginated
from cartography.intel.wiz.api import graphql_query


class FakeResponse:
    def __init__(self, payload, status_error=None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.responses.pop(0)


@pytest.fixture  # type: ignore[misc]
def wiz_api() -> Iterator[tuple[str, list[int]]]:
    statuses: list[int] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers["Content-Length"]))
            status = statuses.pop(0)
            body = b'{"data": {"ok": true}}'
            self.send_response(status)
            if status == 429:
                self.send_header("Retry-After", "1")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/graphql", statuses
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_graphql_query_retries_transient_failure(wiz_api, mocker, status):
    url, statuses = wiz_api
    statuses.extend([status, status, 200])
    mocker.patch("urllib3.util.retry.time.sleep")

    data = graphql_query(build_session(), url, "token", "query {}", {})

    assert data == {"ok": True}
    assert statuses == []


def test_graphql_query_raises_when_rate_limit_persists(wiz_api, mocker):
    url, statuses = wiz_api
    statuses.extend([429] * 7)
    mocker.patch("urllib3.util.retry.time.sleep")

    with pytest.raises(requests.HTTPError, match="429"):
        graphql_query(build_session(), url, "token", "query {}", {})

    assert statuses == []


def test_get_access_token_uses_client_credentials_payload():
    session = FakeSession([FakeResponse({"access_token": "token-1"})])

    token = get_access_token(
        session,
        "https://auth.app.wiz.io/oauth/token",
        "client-id",
        "client-secret",
    )

    assert token == "token-1"
    _, kwargs = session.calls[0]
    assert kwargs["data"] == {
        "grant_type": "client_credentials",
        "audience": "wiz-api",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }


def test_get_paginated_yields_each_page_and_passes_cursor():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "cloudResourcesV2": {
                            "nodes": [{"id": "resource-1"}, {"id": "resource-2"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "cloudResourcesV2": {
                            "nodes": [{"id": "resource-3"}],
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": None,
                            },
                        },
                    },
                },
            ),
        ],
    )

    pages = get_paginated(
        session,
        "https://api.us1.app.wiz.io/graphql",
        "token-1",
        "query Test { cloudResourcesV2 { nodes { id } } }",
        "cloudResourcesV2",
        filter_by={"updatedAt": {"after": "2026-01-01T00:00:00Z"}},
    )

    first_page = next(pages)
    assert len(session.calls) == 1
    assert [first_page, *pages] == [
        [{"id": "resource-1"}, {"id": "resource-2"}],
        [{"id": "resource-3"}],
    ]
    assert session.calls[0][1]["json"]["variables"]["after"] is None
    assert session.calls[1][1]["json"]["variables"]["after"] == "cursor-1"


def test_get_paginated_raises_on_graphql_errors():
    session = FakeSession([FakeResponse({"errors": [{"message": "bad query"}]})])

    with pytest.raises(RuntimeError):
        list(
            get_paginated(
                session,
                "https://api.us1.app.wiz.io/graphql",
                "token-1",
                "query Test { cloudResourcesV2 { nodes { id } } }",
                "cloudResourcesV2",
            )
        )


def test_get_paginated_raises_when_next_page_has_no_cursor():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "cloudResourcesV2": {
                            "nodes": [{"id": "resource-1"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": None,
                            },
                        },
                    },
                },
            ),
        ],
    )

    with pytest.raises(RuntimeError, match="omitted endCursor"):
        list(
            get_paginated(
                session,
                "https://api.us1.app.wiz.io/graphql",
                "token-1",
                "query Test { cloudResourcesV2 { nodes { id } } }",
                "cloudResourcesV2",
            )
        )

    assert len(session.calls) == 1


def test_get_paginated_raises_when_cursor_repeats():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "cloudResourcesV2": {
                            "nodes": [{"id": "resource-1"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "cloudResourcesV2": {
                            "nodes": [{"id": "resource-2"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        },
                    },
                },
            ),
        ],
    )

    with pytest.raises(RuntimeError, match="repeated pagination cursor cursor-1"):
        list(
            get_paginated(
                session,
                "https://api.us1.app.wiz.io/graphql",
                "token-1",
                "query Test { cloudResourcesV2 { nodes { id } } }",
                "cloudResourcesV2",
            )
        )


def test_get_paginated_logs_progress_every_ten_pages(caplog):
    responses = []
    for page in range(10):
        responses.append(
            FakeResponse(
                {
                    "data": {
                        "configurationFindings": {
                            "nodes": [{"id": f"finding-{page}"}],
                            "pageInfo": {
                                "hasNextPage": page < 9,
                                "endCursor": f"cursor-{page}",
                            },
                        },
                    },
                },
            ),
        )
    session = FakeSession(responses)

    with caplog.at_level(logging.INFO, logger="cartography.intel.wiz.api"):
        list(
            get_paginated(
                session,
                "https://api.us1.app.wiz.io/graphql",
                "token-1",
                "query Test { configurationFindings { nodes { id } } }",
                "configurationFindings",
                progress_label="configuration findings",
            )
        )

    assert (
        "Fetched 10 Wiz configuration findings across 10 page(s) so far." in caplog.text
    )


def test_get_issues_uses_status_changed_filter_when_since_is_set():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "issuesV2": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
        ],
    )

    list(
        cartography.intel.wiz.issues.get(
            session,
            "https://api.us1.app.wiz.io/graphql",
            "token-1",
            "2026-01-01T00:00:00Z",
        )
    )

    variables = session.calls[0][1]["json"]["variables"]
    assert variables["filterBy"]["statusChangedAt"] == {
        "after": "2026-01-01T00:00:00Z",
    }
    assert variables["filterBy"]["status"] == [
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "REJECTED",
    ]
    assert "createdAt" not in variables["filterBy"]


@pytest.mark.parametrize(
    ("active_only", "expected_statuses"),
    [
        (True, ["OPEN", "IN_PROGRESS"]),
        (False, ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"]),
    ],
)
def test_get_issues_full_sync_statuses(active_only, expected_statuses):
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "issuesV2": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
        ],
    )

    list(
        cartography.intel.wiz.issues.get(
            session,
            "https://api.us1.app.wiz.io/graphql",
            "token-1",
            None,
            active_only=active_only,
        )
    )

    filter_by = session.calls[0][1]["json"]["variables"]["filterBy"]
    assert filter_by["status"] == expected_statuses
    assert "createdAt" not in filter_by
    assert "updatedAt" not in filter_by
    assert "statusChangedAt" not in filter_by


def test_get_findings_uses_updated_at_filters_without_order_by():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "vulnerabilityFindings": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "configurationFindings": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "detections": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
        ],
    )

    list(
        cartography.intel.wiz.findings.get(
            session,
            "https://api.us1.app.wiz.io/graphql",
            "token-1",
            "2026-01-01T00:00:00Z",
        )
    )

    variables = [call[1]["json"]["variables"] for call in session.calls]
    assert variables[0]["filterBy"] == {
        "updatedAt": {"after": "2026-01-01T00:00:00Z"},
    }
    assert variables[1]["filterBy"]["updatedAt"] == {
        "after": "2026-01-01T00:00:00Z",
    }
    assert variables[1]["filterBy"]["result"] == ["FAIL"]
    assert variables[1]["filterBy"]["status"] == [
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "REJECTED",
    ]
    assert "firstSeenAt" not in variables[1]["filterBy"]
    assert variables[2]["filterBy"]["updatedAt"] == {
        "after": "2026-01-01T00:00:00Z",
    }
    assert all("orderBy" not in variable for variable in variables)

    detection_query = session.calls[2][1]["json"]["query"]
    assert "description(format: MARKDOWN)" not in detection_query
    assert "triggeringEvents" not in detection_query


@pytest.mark.parametrize(
    (
        "active_only",
        "expected_vulnerability_filter",
        "expected_configuration_statuses",
    ),
    [
        (True, {"status": ["OPEN"]}, ["OPEN", "IN_PROGRESS"]),
        (False, None, ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"]),
    ],
)
def test_get_findings_full_sync_statuses(
    active_only,
    expected_vulnerability_filter,
    expected_configuration_statuses,
):
    session = FakeSession(
        [
            FakeResponse(
                {
                    "data": {
                        "vulnerabilityFindings": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "configurationFindings": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
            FakeResponse(
                {
                    "data": {
                        "detections": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            ),
        ],
    )

    list(
        cartography.intel.wiz.findings.get(
            session,
            "https://api.us1.app.wiz.io/graphql",
            "token-1",
            None,
            active_only=active_only,
        )
    )

    vulnerability_filter = session.calls[0][1]["json"]["variables"].get("filterBy")
    assert vulnerability_filter == expected_vulnerability_filter
    filter_by = session.calls[1][1]["json"]["variables"]["filterBy"]
    assert filter_by["result"] == ["FAIL"]
    assert filter_by["status"] == expected_configuration_statuses
    assert "updatedAt" not in filter_by
