import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.cai import get_gcp_roles_cai
from cartography.intel.gcp.cai import get_gcp_service_accounts_cai


def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    content = json.dumps({"error": {"code": status}}).encode("utf-8")
    return HttpError(resp=resp, content=content)


CAI_GETTERS = [
    (get_gcp_service_accounts_cai, ("test-project",)),
    (get_gcp_roles_cai, ("test-project",)),
]


@pytest.mark.parametrize("func,args", CAI_GETTERS)
@patch("time.sleep", return_value=None)
def test_cai_getter_retries_transient_http_error(mock_sleep, func, args):
    # A retryable 5xx on the first execute must be retried (matching every other
    # GCP module, which routes list calls through gcp_api_execute_with_retry)
    # rather than aborting the sync.
    cai_client = MagicMock()
    request = MagicMock()
    request.execute.side_effect = [
        _http_error(503),
        {"assets": [{"resource": {"data": {"id": "asset-1"}}}]},
    ]
    cai_client.assets.return_value.list.return_value = request
    cai_client.assets.return_value.list_next.return_value = None

    result = func(cai_client, *args)

    assert result == [{"id": "asset-1"}]
    assert request.execute.call_count == 2  # retried once after the 503


@pytest.mark.parametrize("func,args", CAI_GETTERS)
@patch("time.sleep", return_value=None)
def test_cai_getter_does_not_retry_non_retryable_error(mock_sleep, func, args):
    # A non-retryable error (e.g. 404) must propagate immediately, not be retried.
    cai_client = MagicMock()
    request = MagicMock()
    request.execute.side_effect = _http_error(404)
    cai_client.assets.return_value.list.return_value = request
    cai_client.assets.return_value.list_next.return_value = None

    with pytest.raises(HttpError):
        func(cai_client, *args)
    assert request.execute.call_count == 1
