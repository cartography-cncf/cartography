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
    Fake httplib2.Http that records request URIs and answers each request with
    the next of the given JSON bodies.
    """

    def __init__(self, bodies=(b"{}",)):
        self.uris = []
        self._bodies = list(bodies)

    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        self.uris.append(uri)
        return httplib2.Response({"status": "200"}), self._bodies.pop(0)


def _build_compute_client(http):
    # Swap only the transport; the client itself comes from build_client(), so it
    # validates requests against the same discovery document as a live sync.
    with patch(
        "cartography.intel.gcp.clients._authorized_http_with_timeout",
        return_value=http,
    ):
        return build_client("compute", "v1", credentials=AnonymousCredentials())


def test_vpn_gateways_request_passes_bundled_discovery_validation():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    get_gcp_vpn_gateways("test-project", compute)

    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true",
    ]


def test_vpn_tunnels_request_passes_bundled_discovery_validation():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    get_gcp_vpn_tunnels("test-project", compute)

    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnTunnels?alt=json&returnPartialSuccess=true",
    ]


def test_ssl_policies_request_passes_bundled_discovery_validation():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    get_gcp_ssl_policies("test-project", compute)

    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/sslPolicies?alt=json&returnPartialSuccess=true",
    ]


def test_target_https_proxies_request_passes_bundled_discovery_validation():
    http = _RecordingHttp()
    compute = _build_compute_client(http)

    get_gcp_target_https_proxies("test-project", compute)

    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/targetHttpsProxies?alt=json&returnPartialSuccess=true",
    ]


def test_next_page_request_keeps_return_partial_success():
    http = _RecordingHttp(
        bodies=[b'{"nextPageToken": "page-2"}', b"{}"],
    )
    compute = _build_compute_client(http)

    get_gcp_vpn_gateways("test-project", compute)

    assert http.uris == [
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true",
        "https://compute.googleapis.com/compute/v1/projects/test-project/aggregated/vpnGateways?alt=json&returnPartialSuccess=true&pageToken=page-2",
    ]
