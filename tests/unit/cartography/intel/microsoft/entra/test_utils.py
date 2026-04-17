import pytest

from cartography.intel.microsoft.clouds import CHINA
from cartography.intel.microsoft.clouds import COMMERCIAL
from cartography.intel.microsoft.clouds import USGOV
from cartography.intel.microsoft.clouds import USGOV_DOD
from cartography.intel.microsoft.entra.utils import build_graph_client


@pytest.mark.parametrize(
    "cloud",
    [COMMERCIAL, USGOV, USGOV_DOD, CHINA],
)
def test_build_graph_client_wires_cloud_endpoints(cloud):
    """The Graph client's adapter base_url and the credential's authority
    must be driven by the supplied cloud; no commercial-cloud defaults
    should leak through when a non-commercial cloud is requested.
    """
    client = build_graph_client(
        tenant_id="00000000-0000-0000-0000-000000000000",
        client_id="cid",
        client_secret="sec",
        cloud=cloud,
    )
    assert client.request_adapter.base_url == cloud.graph_base_url


def test_build_graph_client_default_matches_sdk_default():
    """Zero-change guarantee for commercial-cloud callers: the base_url
    we set must match what the msgraph SDK would pick on its own.
    """
    from azure.identity import ClientSecretCredential
    from msgraph import GraphServiceClient

    default_client = GraphServiceClient(
        ClientSecretCredential(tenant_id="t", client_id="c", client_secret="s"),
        scopes=["https://graph.microsoft.com/.default"],
    )
    commercial_client = build_graph_client("t", "c", "s", COMMERCIAL)
    assert (
        commercial_client.request_adapter.base_url
        == default_client.request_adapter.base_url
    )
