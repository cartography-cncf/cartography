from unittest.mock import Mock

import pytest
import requests

import cartography.intel.databricks.ip_access_lists


def test_ip_access_lists_feature_disabled_returns_empty():
    """Standard-tier workspaces return 404 FEATURE_DISABLED; treat as no lists."""
    api_session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 404
    response.json.return_value = {
        "error_code": "FEATURE_DISABLED",
        "message": "IP access list is not available in the pricing tier of this workspace",
    }
    api_session.get.side_effect = requests.HTTPError(response=response)

    assert cartography.intel.databricks.ip_access_lists.get(api_session) == []


def test_ip_access_lists_other_http_error_propagates():
    """Any other HTTP error must surface; we only swallow FEATURE_DISABLED."""
    api_session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 500
    response.json.return_value = {"error_code": "INTERNAL_ERROR", "message": "boom"}
    api_session.get.side_effect = requests.HTTPError(response=response)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.ip_access_lists.get(api_session)
