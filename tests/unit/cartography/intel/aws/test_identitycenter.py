from unittest.mock import MagicMock

import botocore.exceptions
import pytest

from cartography.intel.aws.identitycenter import (
    _is_permission_set_sync_unsupported_error,
)
from cartography.intel.aws.identitycenter import get_permission_sets
from cartography.intel.aws.identitycenter import get_user_permissionsets
from cartography.intel.aws.identitycenter import PermissionSetSyncNotSupported
from cartography.intel.aws.util.botocore_config import get_botocore_config


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
    mock_session.client.assert_called_once_with(
        "sso-admin",
        region_name="us-east-1",
        config=get_botocore_config(),
    )
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
    mock_session.client.assert_called_once_with(
        "sso-admin",
        region_name="us-east-1",
        config=get_botocore_config(),
    )
    mock_client.get_paginator.assert_called_once_with(
        "list_account_assignments_for_principal",
    )
    mock_paginator.paginate.assert_called_once_with(
        InstanceArn="arn:aws:sso:::instance/test",
        PrincipalId="test-user-id",
        PrincipalType="USER",
    )


@pytest.mark.parametrize(
    ("code", "message", "expected"),
    [
        # The ValidationException for unsupported instances is recognized.
        pytest.param(
            "ValidationException",
            "The operation is not supported for this Identity Center instance",
            True,
            id="unsupported_instance",
        ),
        # The AWS account-instance specific unsupported wording is recognized.
        pytest.param(
            "ValidationException",
            "This operation is not supported for account instances of IAM Identity Center.",
            True,
            id="account_instance_wording",
        ),
        # Other ValidationExceptions are not treated as unsupported instance errors.
        pytest.param(
            "ValidationException",
            "Some other validation error",
            False,
            id="other_validation_error",
        ),
        # AccessDeniedException is not treated as an unsupported instance error.
        pytest.param(
            "AccessDeniedException",
            "Access Denied",
            False,
            id="access_denied",
        ),
    ],
)
def test_is_permission_set_sync_unsupported_error(code, message, expected):
    # Arrange
    error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": code,
                "Message": message,
            },
        },
        operation_name="ListPermissionSets",
    )

    # Act / Assert
    assert _is_permission_set_sync_unsupported_error(error) is expected


def test_get_permission_sets_raises_non_retryable_error_for_unsupported_instance():
    error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "The operation is not supported for this Identity Center instance",
            }
        },
        operation_name="ListPermissionSets",
    )

    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.side_effect = error

    with pytest.raises(PermissionSetSyncNotSupported) as excinfo:
        get_permission_sets(
            mock_session,
            "arn:aws:sso:::instance/ssoins-unsupported",
            "us-east-1",
        )

    assert excinfo.value.__cause__ is error
