import pytest

from cartography.intel.microsoft.clouds import CHINA
from cartography.intel.microsoft.clouds import COMMERCIAL
from cartography.intel.microsoft.clouds import DEFAULT_CLOUD_NAME
from cartography.intel.microsoft.clouds import get_cloud
from cartography.intel.microsoft.clouds import USGOV
from cartography.intel.microsoft.clouds import USGOV_DOD


def test_default_cloud_is_commercial():
    assert DEFAULT_CLOUD_NAME == "commercial"
    assert get_cloud(None) is COMMERCIAL
    assert get_cloud("") is COMMERCIAL


@pytest.mark.parametrize(
    "name,expected",
    [
        ("commercial", COMMERCIAL),
        ("COMMERCIAL", COMMERCIAL),
        ("usgov", USGOV),
        ("usgov-dod", USGOV_DOD),
        ("china", CHINA),
    ],
)
def test_get_cloud_resolves_known_names(name, expected):
    assert get_cloud(name) is expected


def test_get_cloud_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown Microsoft cloud"):
        get_cloud("azurestack")


@pytest.mark.parametrize(
    "cloud,graph_host,authority",
    [
        (COMMERCIAL, "graph.microsoft.com", "login.microsoftonline.com"),
        (USGOV, "graph.microsoft.us", "login.microsoftonline.us"),
        (USGOV_DOD, "dod-graph.microsoft.us", "login.microsoftonline.us"),
        (CHINA, "microsoftgraph.chinacloudapi.cn", "login.chinacloudapi.cn"),
    ],
)
def test_cloud_endpoints_match_microsoft_docs(cloud, graph_host, authority):
    """Pin the endpoints to https://learn.microsoft.com/en-us/graph/deployments."""
    assert cloud.graph_base_url == f"https://{graph_host}/v1.0/"
    assert cloud.graph_scope == f"https://{graph_host}/.default"
    assert cloud.authority == f"https://{authority}"
