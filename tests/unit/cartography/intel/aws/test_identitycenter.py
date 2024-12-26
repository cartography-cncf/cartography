from unittest.mock import MagicMock

import botocore.exceptions

from cartography.intel.aws.identitycenter import get_permission_sets


def test_get_permission_sets_access_denied():
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()

    # Arrange: Set up the mock chain
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator

    # Make paginate raise AccessDeniedException (simulate issue #1415)
    mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
        operation_name='ListPermissionSets',
    )

    # Act: Call the function
    result = get_permission_sets(mock_session, "arn:aws:sso:::instance/test", "us-east-1")

    # Assert:Verify we got an empty list
    assert result == []

    # Verify our mocks were called as expected
    mock_session.client.assert_called_once_with('sso-admin', region_name='us-east-1')
    mock_client.get_paginator.assert_called_once_with('list_permission_sets')
    mock_paginator.paginate.assert_called_once_with(InstanceArn="arn:aws:sso:::instance/test")
