from unittest.mock import MagicMock

import botocore.exceptions

from cartography.intel.aws.identitycenter import (
    _is_permission_set_sync_unsupported_error,
)
from cartography.intel.aws.identitycenter import get_permission_sets
from cartography.intel.aws.identitycenter import get_user_permissionsets


def test_get_permission_sets_access_denied():
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()

    # Arrange: Set up the mock chain
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator

    # Make paginate raise AccessDeniedException (simulate issue #1415)
    mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "AccessDeniedException", "Message": "Access Denied"},
        },
        operation_name="ListPermissionSets",
    )

    # Act: Call the function
    result = get_permission_sets(
        mock_session,
        "arn:aws:sso:::instance/test",
        "us-east-1",
    )

    # Assert:Verify we got an empty list
    assert result == []

    # Verify our mocks were called as expected
    mock_session.client.assert_called_once_with("sso-admin", region_name="us-east-1")
    mock_client.get_paginator.assert_called_once_with("list_permission_sets")
    mock_paginator.paginate.assert_called_once_with(
        InstanceArn="arn:aws:sso:::instance/test",
    )


def test_get_role_assignments_access_denied():
    # Ensure we gracefully handle access denied exceptions for identity center.
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    users = [{"UserId": "test-user-id"}]

    # Arrange: Set up the mock chain
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator

    # Make paginate raise AccessDeniedException (simulate issue #1415)
    mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {"Code": "AccessDeniedException", "Message": "Access Denied"},
        },
        operation_name="ListAccountAssignmentsForPrincipal",
    )

    # Act: Call the function
    result = get_user_permissionsets(
        mock_session,
        users,
        "arn:aws:sso:::instance/test",
        "us-east-1",
    )

    # Assert:Verify we got an empty list
    assert result == []

    # Verify our mocks were called as expected
    mock_session.client.assert_called_once_with("sso-admin", region_name="us-east-1")
    mock_client.get_paginator.assert_called_once_with(
        "list_account_assignments_for_principal",
    )
    mock_paginator.paginate.assert_called_once_with(
        InstanceArn="arn:aws:sso:::instance/test",
        PrincipalId="test-user-id",
        PrincipalType="USER",
    )


def test_is_permission_set_sync_unsupported_error():
    """Test that we correctly identify the ValidationException for unsupported instances."""
    error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "The operation is not supported for this Identity Center instance",
            },
        },
        operation_name="ListPermissionSets",
    )

    assert _is_permission_set_sync_unsupported_error(error)


def test_is_permission_set_sync_unsupported_error_returns_false_for_other_errors():
    """Test that other ValidationExceptions are not treated as unsupported instance errors."""
    error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "Some other validation error",
            },
        },
        operation_name="ListPermissionSets",
    )

    assert not _is_permission_set_sync_unsupported_error(error)


def test_is_permission_set_sync_unsupported_error_returns_false_for_access_denied():
    """Test that AccessDeniedException is not treated as unsupported instance error."""
    error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Access Denied",
            },
        },
        operation_name="ListPermissionSets",
    )

    assert not _is_permission_set_sync_unsupported_error(error)
