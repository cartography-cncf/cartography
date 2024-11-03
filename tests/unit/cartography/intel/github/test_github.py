import typing
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone as tz
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import HTTPError

from cartography.intel.github.util import _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import handle_rate_limit_sleep
from tests.data.github.rate_limit import RATE_LIMIT_RESPONSE_JSON


@patch('cartography.intel.github.util.time.sleep')
@patch('cartography.intel.github.util.handle_rate_limit_sleep')
@patch('cartography.intel.github.util.fetch_page')
def test_fetch_all_handles_retries(
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    '''
    Ensures that fetch_all re-reaises the same exceptions when exceeding retry limit
    '''
    # Arrange
    exception = HTTPError
    response = Response()
    response.status_code = 500
    mock_fetch_page.side_effect = exception('my-error', response=response)
    retries = 3
    # Act
    with pytest.raises(exception) as excinfo:
        fetch_all('my-token', 'my-api_url', 'my-org', 'my-query', 'my-resource', retries=retries)
    # Assert
    assert mock_handle_rate_limit_sleep.call_count == retries
    assert mock_fetch_page.call_count == retries
    assert 'my-error' in str(excinfo.value)


@typing.no_type_check
@patch('cartography.intel.github.util.time.sleep')
@patch('cartography.intel.github.util.datetime')
@patch('cartography.intel.github.util.requests.get')
def test_handle_rate_limit_sleep(
    mock_requests_get: Mock,
    mock_datetime: Mock,
    mock_sleep: Mock,
) -> None:
    '''
    Ensure we sleep to avoid the rate limit
    '''
    # Arrange
    mock_datetime.fromtimestamp = datetime.fromtimestamp
    now = datetime(year=2040, month=1, day=1, hour=19, minute=0, second=0, tzinfo=tz.utc)
    mock_datetime.now = Mock(return_value=now)
    reset = (now + timedelta(minutes=47)).timestamp()
    # sleep for one extra minute for safety
    expected_sleep_seconds = timedelta(minutes=48).seconds

    # above threshold
    resp_0 = deepcopy(RATE_LIMIT_RESPONSE_JSON)
    resp_0['resources']['graphql']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD + 1
    resp_0['resources']['graphql']['reset'] = reset

    # below threshold
    resp_1 = deepcopy(RATE_LIMIT_RESPONSE_JSON)
    resp_1['resources']['graphql']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD - 1
    resp_1['resources']['graphql']['reset'] = reset

    mock_requests_get.side_effect = [
        Mock(json=Mock(return_value=resp_0)),
        Mock(json=Mock(return_value=resp_1)),
    ]

    # Act
    handle_rate_limit_sleep('my-token')
    # Assert
    mock_datetime.now.assert_not_called()
    mock_sleep.assert_not_called()

    # reset mocks
    mock_datetime.reset_mock()
    mock_sleep.reset_mock()

    # Act
    handle_rate_limit_sleep('my-token')
    # Assert
    mock_datetime.now.assert_called_once_with(tz.utc)
    mock_sleep.assert_called_once_with(expected_sleep_seconds)
