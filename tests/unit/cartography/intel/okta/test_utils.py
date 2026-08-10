import json
import time
from unittest import mock

import pytest

from cartography.intel.okta.utils import check_rate_limit
from cartography.intel.okta.utils import okta_paged_request_with_retry
from tests.data.okta.utils import create_long_timeout_response
from tests.data.okta.utils import create_response
from tests.data.okta.utils import create_throttled_response


@mock.patch.object(time, "sleep", return_value=None)
def test_utils_rate_limit_not_reached(mock_sleep: mock.MagicMock):
    response = create_response()

    check_rate_limit(response)

    mock_sleep.assert_not_called()


@mock.patch.object(time, "sleep", return_value=None)
def test_utils_rate_limit_reached(mock_sleep: mock.MagicMock):
    response = create_throttled_response()
    check_rate_limit(response)

    expected = 3

    mock_sleep.assert_called_with(expected)


def test_utils_log_rate_limit_reset():
    response = create_long_timeout_response()

    with pytest.raises(Exception):
        check_rate_limit(response)


@mock.patch.object(time, "sleep", return_value=None)
def test_paged_request_retries_non_json_error(mock_sleep: mock.MagicMock):
    response = create_response()
    request = mock.MagicMock(
        side_effect=[json.JSONDecodeError("Expecting value", "", 0), response]
    )

    assert okta_paged_request_with_retry(request, "testing") is response
    assert request.call_count == 2
    mock_sleep.assert_called_once_with(1)


@mock.patch.object(time, "sleep", return_value=None)
def test_paged_request_raises_after_retries(mock_sleep: mock.MagicMock):
    request = mock.MagicMock(side_effect=json.JSONDecodeError("Expecting value", "", 0))

    with pytest.raises(json.JSONDecodeError):
        okta_paged_request_with_retry(request, "testing")

    assert request.call_count == 3
    assert mock_sleep.call_count == 2
