import pytest

from cartography.intel.wiz.api import get_access_token
from cartography.intel.wiz.api import get_paginated


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


def test_get_paginated_collects_all_nodes_and_passes_cursor():
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
                                "hasNextPage": False,
                                "endCursor": None,
                            },
                        },
                    },
                },
            ),
        ],
    )

    nodes = get_paginated(
        session,
        "https://api.us1.app.wiz.io/graphql",
        "token-1",
        "query Test { cloudResourcesV2 { nodes { id } } }",
        "cloudResourcesV2",
        filter_by={"updatedAt": {"after": "2026-01-01T00:00:00Z"}},
    )

    assert nodes == [{"id": "resource-1"}, {"id": "resource-2"}]
    assert session.calls[0][1]["json"]["variables"]["after"] is None
    assert session.calls[1][1]["json"]["variables"]["after"] == "cursor-1"


def test_get_paginated_raises_on_graphql_errors():
    session = FakeSession([FakeResponse({"errors": [{"message": "bad query"}]})])

    with pytest.raises(RuntimeError):
        get_paginated(
            session,
            "https://api.us1.app.wiz.io/graphql",
            "token-1",
            "query Test { cloudResourcesV2 { nodes { id } } }",
            "cloudResourcesV2",
        )
