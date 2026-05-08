from datetime import datetime
from datetime import timezone

import cartography.intel.aws.organizations
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
            "inscope": True,
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
    assert result[0]["inscope"] is True


def test_transform_aws_organization_accounts_marks_suspended_out_of_scope():
    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization_accounts(
        TEST_ORGANIZATION_ACCOUNTS[2:3],
        "o-exampleorgid",
    )

    # Assert
    assert result[0]["state"] == "SUSPENDED"
    assert result[0]["inscope"] is False


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
            "id": "r-exam",
            "arn": "arn:aws:organizations::111111111111:root/o-exampleorgid/r-exam",
            "name": "Root",
            "org_id": "o-exampleorgid",
            "child_ou_ids": ["ou-exam-a1b2c3d4"],
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
            "id": "ou-exam-b2c3d4e5",
            "arn": "arn:aws:organizations::111111111111:ou/o-exampleorgid/ou-exam-b2c3d4e5",
            "name": "Logging",
            "org_id": "o-exampleorgid",
            "root_id": "r-exam",
            "parent_root_id": None,
            "parent_ou_id": "ou-exam-a1b2c3d4",
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
