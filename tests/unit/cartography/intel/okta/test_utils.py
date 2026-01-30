import time
from unittest import mock

import pytest

from cartography.intel.okta.utils import check_rate_limit
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
