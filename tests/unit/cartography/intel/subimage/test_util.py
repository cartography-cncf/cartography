import pytest
from requests.adapters import HTTPAdapter

from cartography.intel.subimage.util import create_api_session


@pytest.mark.parametrize(
    "base_url",
    ["https://app.example.com", "http://backend.example.svc:8000"],
)
def test_create_api_session_retries_on_both_schemes(base_url):
    session = create_api_session("token")

    adapter = session.get_adapter(base_url)
    assert isinstance(adapter, HTTPAdapter)
    assert adapter.max_retries.total == 5
    assert 503 in adapter.max_retries.status_forcelist
