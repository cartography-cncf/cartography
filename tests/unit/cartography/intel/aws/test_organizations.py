from datetime import datetime
from datetime import timezone

import cartography.intel.aws.organizations
from tests.data.aws.organizations import TEST_ORGANIZATION
from tests.data.aws.organizations import TEST_ORGANIZATION_ACCOUNTS


def test_transform_aws_organization_keeps_expected_describe_organization_shape():
    # Arrange
    account_ids = ["111111111111", "222222222222"]

    # Act
    result = cartography.intel.aws.organizations.transform_aws_organization(
        TEST_ORGANIZATION,
        account_ids,
    )

    # Assert
    assert result == {
        "id": "o-exampleorgid",
        "arn": "arn:aws:organizations::111111111111:organization/o-exampleorgid",
        "feature_set": "ALL",
        "management_account_arn": "arn:aws:organizations::111111111111:account/o-exampleorgid/111111111111",
        "management_account_id": "111111111111",
        "management_account_email": "management@example.com",
        "account_ids": account_ids,
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
