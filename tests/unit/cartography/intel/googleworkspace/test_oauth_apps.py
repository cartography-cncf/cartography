import sys
import types
from pathlib import Path


def _stub_googleapiclient() -> None:
    googleapiclient = types.ModuleType("googleapiclient")
    discovery = types.ModuleType("googleapiclient.discovery")
    errors = types.ModuleType("googleapiclient.errors")
    discovery.Resource = object
    errors.HttpError = Exception
    googleapiclient.discovery = discovery
    googleapiclient.errors = errors
    sys.modules["googleapiclient"] = googleapiclient
    sys.modules["googleapiclient.discovery"] = discovery
    sys.modules["googleapiclient.errors"] = errors

    neo4j = types.ModuleType("neo4j")
    neo4j.Session = object
    neo4j_exceptions = types.ModuleType("neo4j.exceptions")

    class _ClientError(Exception):
        pass

    class _ServiceUnavailable(Exception):
        pass

    class _SessionExpired(Exception):
        pass

    class _TransientError(Exception):
        pass

    neo4j_exceptions.ClientError = _ClientError
    neo4j_exceptions.ServiceUnavailable = _ServiceUnavailable
    neo4j_exceptions.SessionExpired = _SessionExpired
    neo4j_exceptions.TransientError = _TransientError
    neo4j.exceptions = neo4j_exceptions
    sys.modules["neo4j"] = neo4j
    sys.modules["neo4j.exceptions"] = neo4j_exceptions

    backoff = types.ModuleType("backoff")

    def _expo(**_: object):
        while True:
            yield 0

    def _on_exception(*_: object, **__: object):
        def decorator(func):
            return func

        return decorator

    backoff.expo = _expo
    backoff.on_exception = _on_exception
    sys.modules["backoff"] = backoff

    cartography_util = types.ModuleType("cartography.util")

    def _timeit(func):
        return func

    cartography_util.timeit = _timeit
    cartography_util.backoff_handler = lambda *args, **kwargs: None
    sys.modules["cartography.util"] = cartography_util

    cartography_client = sys.modules.get("cartography.client") or types.ModuleType("cartography.client")
    cartography_client_core = types.ModuleType("cartography.client.core")
    tx_module = types.ModuleType("cartography.client.core.tx")
    tx_module.load = lambda *args, **kwargs: None
    tx_module.load_matchlinks = lambda *args, **kwargs: None
    cartography_client.core = cartography_client_core
    cartography_client_core.tx = tx_module
    sys.modules["cartography.client"] = cartography_client
    sys.modules["cartography.client.core"] = cartography_client_core
    sys.modules["cartography.client.core.tx"] = tx_module

    cartography_graph = types.ModuleType("cartography.graph")
    graph_job_module = types.ModuleType("cartography.graph.job")

    class _GraphJob:
        @classmethod
        def from_node_schema(cls, *args, **kwargs):
            return cls()

        @classmethod
        def from_matchlink(cls, *args, **kwargs):
            return cls()

        def run(self, *args, **kwargs):
            return None

    graph_job_module.GraphJob = _GraphJob
    cartography_graph.job = graph_job_module
    sys.modules["cartography.graph"] = cartography_graph
    sys.modules["cartography.graph.job"] = graph_job_module

    googleworkspace_pkg = types.ModuleType("cartography.intel.googleworkspace")
    googleworkspace_pkg.__path__ = [
        str(Path(__file__).resolve().parents[5] / "cartography/intel/googleworkspace"),
    ]
    sys.modules["cartography.intel.googleworkspace"] = googleworkspace_pkg

    google = types.ModuleType("google")
    google_auth = types.ModuleType("google.auth")
    google_auth.default = lambda: (None, None)
    google_auth_exceptions = types.ModuleType("google.auth.exceptions")
    google_auth_exceptions.DefaultCredentialsError = Exception
    google_auth_transport = types.ModuleType("google.auth.transport")
    google_auth_transport_requests = types.ModuleType("google.auth.transport.requests")
    google_auth_transport_requests.Request = object
    google_auth_transport.requests = google_auth_transport_requests
    google_oauth2 = types.ModuleType("google.oauth2")
    google_oauth2_credentials = types.ModuleType("google.oauth2.credentials")
    google_oauth2_credentials.Credentials = object
    google_oauth2_service_account = types.ModuleType("google.oauth2.service_account")
    google_oauth2_service_account.Credentials = object
    google_oauth2.credentials = google_oauth2_credentials
    google_oauth2.service_account = google_oauth2_service_account

    google.oauth2 = google_oauth2
    google.auth = google_auth
    sys.modules["google"] = google
    sys.modules["google.auth"] = google_auth
    sys.modules["google.auth.exceptions"] = google_auth_exceptions
    sys.modules["google.auth.transport"] = google_auth_transport
    sys.modules["google.auth.transport.requests"] = google_auth_transport_requests
    sys.modules["google.oauth2"] = google_oauth2
    sys.modules["google.oauth2.credentials"] = google_oauth2_credentials
    sys.modules["google.oauth2.service_account"] = google_oauth2_service_account


_stub_googleapiclient()

from cartography.intel.googleworkspace.oauth_apps import (
    transform_oauth_apps_and_authorizations,
)


def test_transform_appends_risk_metadata():
    tokens = [
        {
            "clientId": "client-1",
            "user_id": "user-1",
            "scopes": [
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/drive",
            ],
        }
    ]

    apps, authorizations = transform_oauth_apps_and_authorizations(tokens)

    assert len(apps) == 1
    assert authorizations[0]["risk_level"] == "high"
    assert "https://www.googleapis.com/auth/drive|high" in authorizations[0]["scope_risk_levels"]


def test_transform_handles_unknown_scope_and_empty_scope_list():
    tokens = [
        {
            "clientId": "client-1",
            "user_id": "user-1",
            "scopes": ["https://www.googleapis.com/auth/unknown"],
        },
        {
            "clientId": "client-2",
            "user_id": "user-2",
            "scopes": [],
        },
    ]

    _, authorizations = transform_oauth_apps_and_authorizations(tokens)

    first_auth = next(auth for auth in authorizations if auth["client_id"] == "client-1")
    second_auth = next(auth for auth in authorizations if auth["client_id"] == "client-2")

    assert first_auth["risk_level"] == "medium"
    assert first_auth["scope_risk_levels"] == ["https://www.googleapis.com/auth/unknown|medium"]

    assert second_auth["risk_level"] == "medium"
    assert second_auth["scope_risk_levels"] == []
