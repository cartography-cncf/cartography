from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

import tests.data.aws.apigateway as test_data
from cartography.intel.aws.apigateway import get_rest_api_resources_methods_integrations
from cartography.intel.aws.apigateway import parse_policy


def test_parse_policy():
    res = parse_policy("1", test_data.DOUBLY_ESCAPED_POLICY)

    assert (res) is not None
    assert (res["api_id"]) is not None
    assert (res["internet_accessible"]) is not None
    assert (res["accessible_actions"]) is not None


def test_none_policy():
    res = parse_policy(None, None)

    assert (res) is None


@patch("time.sleep")
@patch("cartography.intel.aws.apigateway.logger")
@patch("botocore.client.BaseClient.get_paginator")
def test_get_rest_api_resources_retries_on_too_many_requests(
    mock_get_paginator,
    mock_logger,
    mock_sleep,
):
    """
    Test that get_rest_api_resources retries on TooManyRequestsException
    and succeeds on the third attempt.
    """
    # Arrange
    api = {"id": "test-api"}
    client = MagicMock()
    expected_resources = [
        {"id": "resource1", "pathPart": "users"},
        {"id": "resource2", "pathPart": "orders"},
    ]
    too_many_requests_error = ClientError(
        error_response={
            "Error": {"Code": "TooManyRequestsException", "Message": "Rate exceeded"}
        },
        operation_name="GetResources",
    )
    mock_paginator = MagicMock()
    mock_paginator.paginate.side_effect = [
        too_many_requests_error,  # First attempt fails
        too_many_requests_error,  # Second attempt fails
        [{"items": expected_resources}],  # Third attempt succeeds
    ]
    client.get_paginator.return_value = mock_paginator

    # Act
    result = get_rest_api_resources_methods_integrations(api, client)

    # Assert
    assert result[0] == expected_resources

    assert mock_paginator.paginate.call_count == 3
    mock_paginator.paginate.assert_called_with(restApiId="test-api")
    client.get_paginator.assert_called_with("get_resources")
