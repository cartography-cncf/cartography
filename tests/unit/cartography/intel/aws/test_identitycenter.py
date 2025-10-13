from types import ModuleType
from unittest.mock import MagicMock
from unittest.mock import patch

import sys

import botocore.exceptions


def _stub_module(name: str) -> None:
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)


for _module in [
    "types_aiobotocore_ecr",
    "types_aiobotocore_ecr.type_defs",
    "types_aiobotocore_ecr.literals",
    "types_aiobotocore_ecr.client",
]:
    _stub_module(_module)

sys.modules["types_aiobotocore_ecr"].ECRClient = MagicMock()

from cartography.intel.aws.identitycenter import get_permission_sets
from cartography.intel.aws.identitycenter import get_role_assignments
from cartography.intel.aws.identitycenter import (
    _is_permission_set_sync_unsupported_error,
)
from cartography.intel.aws.identitycenter import sync_identity_center_instances


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
    result = get_role_assignments(
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


def test_sync_identity_center_instances_skips_permission_set_sync_when_unsupported():
    neo4j_session = MagicMock()
    boto3_session = MagicMock()
    unsupported_error = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "The operation is not supported for this Identity Center instance",
            }
        },
        operation_name="ListPermissionSets",
    )

    with patch(
        "cartography.intel.aws.identitycenter.get_identity_center_instances",
        return_value=[
            {
                "InstanceArn": "arn:aws:sso:::instance/test",
                "IdentityStoreId": "d-1234567890",
            }
        ],
    ), patch("cartography.intel.aws.identitycenter.load_identity_center_instances"), patch(
        "cartography.intel.aws.identitycenter.get_sso_groups",
        return_value=[],
    ) as get_sso_groups_mock, patch(
        "cartography.intel.aws.identitycenter.get_sso_users",
        return_value=[],
    ) as get_sso_users_mock, patch(
        "cartography.intel.aws.identitycenter.get_user_group_memberships",
        return_value={},
    ) as get_user_group_memberships_mock, patch(
        "cartography.intel.aws.identitycenter.transform_sso_groups",
        return_value=[],
    ) as transform_groups, patch(
        "cartography.intel.aws.identitycenter.load_sso_groups",
    ) as load_groups, patch(
        "cartography.intel.aws.identitycenter.transform_sso_users",
        return_value=[],
    ) as transform_users, patch(
        "cartography.intel.aws.identitycenter.load_sso_users",
    ) as load_users, patch(
        "cartography.intel.aws.identitycenter.load_permission_sets",
    ) as load_permission_sets, patch(
        "cartography.intel.aws.identitycenter.get_group_role_assignments",
    ) as get_group_role_assignments, patch(
        "cartography.intel.aws.identitycenter.get_role_assignments",
    ) as get_role_assignments_mock, patch(
        "cartography.intel.aws.identitycenter.get_permset_roles",
        return_value=[],
    ) as get_permset_roles_mock, patch(
        "cartography.intel.aws.identitycenter.load_role_assignments",
    ) as load_role_assignments_mock, patch(
        "cartography.intel.aws.identitycenter.cleanup",
    ) as cleanup_mock, patch(
        "cartography.intel.aws.identitycenter.get_permission_sets",
        side_effect=unsupported_error,
    ):
        sync_identity_center_instances(
            neo4j_session,
            boto3_session,
            ["us-east-1"],
            "123456789012",
            123,
            {"AWS_ID": "123456789012", "UPDATE_TAG": 123},
        )

    load_permission_sets.assert_not_called()
    get_group_role_assignments.assert_not_called()
    get_role_assignments_mock.assert_not_called()
    get_permset_roles_mock.assert_not_called()
    load_role_assignments_mock.assert_not_called()
    transform_groups.assert_called_once_with([], {})
    load_groups.assert_called_once()
    transform_users.assert_called_once_with([], {}, {})
    load_users.assert_called_once()
    cleanup_mock.assert_called_once_with(
        neo4j_session,
        {"AWS_ID": "123456789012", "UPDATE_TAG": 123},
    )
    get_sso_groups_mock.assert_called_once_with(boto3_session, "d-1234567890", "us-east-1")
    get_sso_users_mock.assert_called_once_with(boto3_session, "d-1234567890", "us-east-1")
    get_user_group_memberships_mock.assert_called_once_with(
        boto3_session,
        "d-1234567890",
        [],
        "us-east-1",
    )
