from datetime import datetime
from datetime import timezone
from unittest import mock

import botocore.exceptions

import cartography.intel.aws.organizations
from cartography.intel.aws.organizations import AWSOrganizationSyncStatus
from tests.data.aws.organizations import TEST_ORGANIZATION
from tests.data.aws.organizations import TEST_ORGANIZATION_ACCOUNTS
from tests.data.aws.organizations import TEST_ORGANIZATION_ROOTS
from tests.data.aws.organizations import TEST_ORGANIZATIONAL_UNITS


def test_transform_aws_organization_keeps_expected_describe_organization_shape():
    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization(
        TEST_ORGANIZATION,
    )

    # Assert
    assert result == {
        "id": "o-exampleorgid",
        "arn": "arn:aws:organizations::111111111111:organization/o-exampleorgid",
        "feature_set": "ALL",
        "management_account_arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
        "management_account_id": "111111111111",
        "management_account_email": "management@example.com",
    }


def test_transform_aws_organization_accounts_preserves_boto3_account_fields():
    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization_accounts(
        TEST_ORGANIZATION_ACCOUNTS[:1],
        "o-exampleorgid",
    )

    # Assert
    assert result == [
        {
            "id": "111111111111",
            "arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
            "email": "management@example.com",
            "name": "management-account",
            "state": "ACTIVE",
            "status": "ACTIVE",
            "joined_method": "CREATED",
            "joined_timestamp": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "org_id": "o-exampleorgid",
        },
    ]


def test_transform_aws_organization_accounts_falls_back_to_legacy_status():
    # Arrange
    account_without_state = {
        key: value
        for key, value in TEST_ORGANIZATION_ACCOUNTS[0].items()
        if key != "State"
    }

    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization_accounts(
        [account_without_state],
        "o-exampleorgid",
    )

    # Assert
    assert result[0]["state"] == "ACTIVE"
    assert result[0]["status"] == "ACTIVE"


def test_transform_aws_organization_accounts_preserves_suspended_state():
    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization_accounts(
        TEST_ORGANIZATION_ACCOUNTS[2:3],
        "o-exampleorgid",
    )

    # Assert
    assert result[0]["state"] == "SUSPENDED"


def test_transform_aws_organization_roots_preserves_root_fields_and_child_ids():
    # Arrange
    root = {
        **TEST_ORGANIZATION_ROOTS[0],
        "child_ou_ids": ["ou-exam-a1b2c3d4"],
        "account_ids": ["111111111111"],
    }

    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization_roots(
        [root],
        "o-exampleorgid",
    )

    # Assert
    assert result == [
        {
            "id": "o-exampleorgid/r-exam",
            "root_id": "r-exam",
            "arn": "arn:aws:organizations::111111111111:root/o-exampleorgid/r-exam",
            "name": "Root",
            "org_id": "o-exampleorgid",
            "child_ou_ids": ["o-exampleorgid/ou-exam-a1b2c3d4"],
            "account_ids": ["111111111111"],
        },
    ]


def test_transform_aws_organizational_units_preserves_parent_fields():
    # Arrange
    organizational_unit = {
        **TEST_ORGANIZATIONAL_UNITS["ou-exam-a1b2c3d4"][0],
        "root_id": "r-exam",
        "parent_root_id": None,
        "parent_ou_id": "ou-exam-a1b2c3d4",
        "child_ou_ids": [],
        "account_ids": ["444444444444"],
    }

    # Act
    result = cartography.intel.aws.organizations.transform_aws_organizational_units(
        [organizational_unit],
        "o-exampleorgid",
    )

    # Assert
    assert result == [
        {
            "id": "o-exampleorgid/ou-exam-b2c3d4e5",
            "ou_id": "ou-exam-b2c3d4e5",
            "arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-b2c3d4e5",
            "name": "Logging",
            "org_id": "o-exampleorgid",
            "root_id": "o-exampleorgid/r-exam",
            "parent_root_id": None,
            "parent_ou_id": "o-exampleorgid/ou-exam-a1b2c3d4",
            "child_ou_ids": [],
            "account_ids": ["444444444444"],
        },
    ]


def test_paginate_aws_organizations_flattens_pages():
    # Arrange
    class FakePaginator:
        def paginate(self, **kwargs):
            return [{"Items": [{"Id": "1"}]}, {"Items": [{"Id": "2"}]}]

    class FakeClient:
        def get_paginator(self, name):
            assert name == "list_things"
            return FakePaginator()

    # Act
    result = cartography.intel.aws.organizations._paginate_aws_organizations(
        FakeClient(),
        "list_things",
        "Items",
        ParentId="r-exam",
    )

    # Assert
    assert result == [{"Id": "1"}, {"Id": "2"}]


def _make_client_error(code: str) -> botocore.exceptions.ClientError:
    return botocore.exceptions.ClientError(
        {"Error": {"Code": code, "Message": code}},
        "OrganizationsOperation",
    )


def test_sync_aws_organization_returns_synced_result():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            return {"Organization": TEST_ORGANIZATION}

    common_job_parameters = {"UPDATE_TAG": 1}

    with (
        mock.patch.object(
            cartography.intel.aws.organizations,
            "get_aws_organization_hierarchy",
            return_value=([TEST_ORGANIZATION_ROOTS[0]], [], TEST_ORGANIZATION_ACCOUNTS),
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_account_nodes_from_organization",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "sync_root_principal",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organization",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organization_roots",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organizational_units",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "cleanup_aws_organization_hierarchy",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "cleanup_stale_aws_account_organization_metadata",
        ),
    ):
        # Act
        result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "111111111111",
            1,
            common_job_parameters,
        )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.SYNCED
    assert result.organization_id == "o-exampleorgid"
    assert common_job_parameters["_SYNCED_AWS_ORGANIZATION_IDS"] == [
        "o-exampleorgid",
    ]


def test_sync_aws_organization_returns_already_synced_result():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            return {"Organization": TEST_ORGANIZATION}

    common_job_parameters = {
        "UPDATE_TAG": 1,
        "_SYNCED_AWS_ORGANIZATION_IDS": ["o-exampleorgid"],
    }

    with mock.patch.object(
        cartography.intel.aws.organizations,
        "get_aws_organization_hierarchy",
    ) as mock_get_hierarchy:
        # Act
        result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "111111111111",
            1,
            common_job_parameters,
        )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.ALREADY_SYNCED
    assert result.organization_id == "o-exampleorgid"
    mock_get_hierarchy.assert_not_called()


def test_sync_aws_organization_second_call_returns_already_synced_result():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            return {"Organization": TEST_ORGANIZATION}

    common_job_parameters = {"UPDATE_TAG": 1}

    with (
        mock.patch.object(
            cartography.intel.aws.organizations,
            "get_aws_organization_hierarchy",
            return_value=([TEST_ORGANIZATION_ROOTS[0]], [], TEST_ORGANIZATION_ACCOUNTS),
        ) as mock_get_hierarchy,
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_account_nodes_from_organization",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "sync_root_principal",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organization",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organization_roots",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_organizational_units",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "cleanup_aws_organization_hierarchy",
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "cleanup_stale_aws_account_organization_metadata",
        ),
    ):
        # Act
        first_result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "111111111111",
            1,
            common_job_parameters,
        )
        second_result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "222222222222",
            1,
            common_job_parameters,
        )

    # Assert
    assert first_result.status == AWSOrganizationSyncStatus.SYNCED
    assert second_result.status == AWSOrganizationSyncStatus.ALREADY_SYNCED
    assert second_result.organization_id == "o-exampleorgid"
    assert mock_get_hierarchy.call_count == 1


def test_sync_aws_organization_returns_not_in_org_result():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            raise _make_client_error("AWSOrganizationsNotInUseException")

    # Act
    result = cartography.intel.aws.organizations.sync_aws_organization(
        mock.Mock(),
        FakeClient(),
        "111111111111",
        1,
        {"UPDATE_TAG": 1},
    )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.NOT_IN_ORG
    assert result.error_code == "AWSOrganizationsNotInUseException"


def test_sync_aws_organization_returns_access_denied_result():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            raise _make_client_error("AccessDeniedException")

    # Act
    result = cartography.intel.aws.organizations.sync_aws_organization(
        mock.Mock(),
        FakeClient(),
        "111111111111",
        1,
        {"UPDATE_TAG": 1},
    )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.ACCESS_DENIED
    assert result.error_code == "AccessDeniedException"


def test_sync_aws_organization_returns_incomplete_result_for_hierarchy_error():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            return {"Organization": TEST_ORGANIZATION}

    with mock.patch.object(
        cartography.intel.aws.organizations,
        "get_aws_organization_hierarchy",
        side_effect=_make_client_error("ThrottlingException"),
    ):
        # Act
        result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "111111111111",
            1,
            {"UPDATE_TAG": 1},
        )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.INCOMPLETE
    assert result.organization_id == "o-exampleorgid"
    assert result.error_code == "ThrottlingException"


def test_sync_aws_organization_returns_incomplete_when_account_state_is_unknown():
    # Arrange
    class FakeClient:
        def describe_organization(self):
            return {"Organization": TEST_ORGANIZATION}

    account_without_state_or_status = {
        key: value
        for key, value in TEST_ORGANIZATION_ACCOUNTS[0].items()
        if key not in {"State", "Status"}
    }

    with (
        mock.patch.object(
            cartography.intel.aws.organizations,
            "get_aws_organization_hierarchy",
            return_value=(
                [TEST_ORGANIZATION_ROOTS[0]],
                [],
                [account_without_state_or_status],
            ),
        ),
        mock.patch.object(
            cartography.intel.aws.organizations,
            "load_aws_account_nodes_from_organization",
        ) as mock_load_accounts,
        mock.patch.object(
            cartography.intel.aws.organizations,
            "cleanup_aws_organization_hierarchy",
        ) as mock_cleanup,
    ):
        # Act
        result = cartography.intel.aws.organizations.sync_aws_organization(
            mock.Mock(),
            FakeClient(),
            "111111111111",
            1,
            {"UPDATE_TAG": 1},
        )

    # Assert
    assert result.status == AWSOrganizationSyncStatus.INCOMPLETE
    assert result.organization_id == "o-exampleorgid"
    mock_load_accounts.assert_not_called()
    mock_cleanup.assert_not_called()
