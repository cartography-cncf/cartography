"""
Build real Compute clients from the discovery document cartography uses.

The other GCP unit tests mock the client, so they cannot notice when a getter
passes a parameter that googleapiclient rejects at request-build time. These
tests run each getter against a client from `build_client()` (the static
discovery document bundled with google-api-python-client), with only the HTTP
transport faked, so an unsupported parameter fails here instead of in a live
sync.
"""

from unittest.mock import patch

import httplib2
from google.auth.credentials import AnonymousCredentials

from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.compute import get_gcp_vpn_gateways
from cartography.intel.gcp.compute import get_gcp_vpn_tunnels
from cartography.intel.gcp.ssl_policy import get_gcp_ssl_policies
from cartography.intel.gcp.target_https_proxy import get_gcp_target_https_proxies


class _RecordingHttp:
    """
    Fake httplib2.Http that records request URIs and answers with the given
    JSON bodies in order, then with `{}`.
    """

    def __init__(self, bodies=()):
        self.uris = []
        self._bodies = list(bodies)

    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        self.uris.append(uri)
        content = self._bodies.pop(0) if self._bodies else b"{}"
        return httplib2.Response({"status": "200"}), content


def _build_compute_client(http):
    with patch(
        "cartography.intel.gcp.clients._authorized_http_with_timeout",
        return_value=http,
    ):
        return build_client("compute", "v1", credentials=AnonymousCredentials())


def test_get_gcp_vpn_gateways_builds_valid_request():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    assert get_gcp_vpn_gateways("test-project", compute) == ([], False)
    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true",
    ]


def test_get_gcp_vpn_tunnels_builds_valid_request():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    assert get_gcp_vpn_tunnels("test-project", compute) == ([], False)
    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnTunnels?alt=json&returnPartialSuccess=true",
    ]


def test_get_gcp_ssl_policies_builds_valid_request():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    assert get_gcp_ssl_policies("test-project", compute) == {
        "id": "projects/test-project/aggregated/sslPolicies",
        "items": {},
    }
    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/sslPolicies?alt=json&returnPartialSuccess=true",
    ]


def test_get_gcp_target_https_proxies_builds_valid_request():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    assert get_gcp_target_https_proxies("test-project", compute) == {
        "id": "projects/test-project/aggregated/targetHttpsProxies",
        "items": {},
    }
    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/targetHttpsProxies?alt=json&returnPartialSuccess=true",
    ]


def test_return_partial_success_is_kept_on_every_page():
    http = _RecordingHttp(
        bodies=[
            b'{"items": {"regions/us-central1": {"vpnGateways": [{"name": "gw-a"}]}},'
            b' "nextPageToken": "page-2"}',
            b'{"items": {"regions/europe-west1": {"vpnGateways": [{"name": "gw-b"}]}}}',
        ],
    )
    compute = _build_compute_client(http)

    assert get_gcp_vpn_gateways("test-project", compute) == (
        [{"name": "gw-a"}, {"name": "gw-b"}],
        False,
    )
    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true",
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true&pageToken=page-2",
    ]
