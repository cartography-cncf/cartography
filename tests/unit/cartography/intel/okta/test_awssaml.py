from typing import Optional
from unittest import mock
from unittest.mock import MagicMock

import cartography.intel.okta.awssaml
from cartography.intel.okta.awssaml import _parse_okta_group_name
from cartography.intel.okta.awssaml import AccountRole
from cartography.intel.okta.awssaml import GroupRole
from cartography.intel.okta.awssaml import OktaGroup
from cartography.intel.okta.awssaml import query_for_okta_to_awssso_role_mapping
from cartography.intel.okta.awssaml import transform_okta_group_to_aws_role


SAMPLE_OKTA_GROUP_IDS = ['00g9oh2', '00g9oh3', '00g9oh4']


def test_saml_with_default_regex():
    group_name = "aws#northamerica-production#Tier1_Support#828416469395"
    group_id = "groupid"
    default_regex = r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$"
    result = transform_okta_group_to_aws_role(group_id, group_name, default_regex)

    assert result
    assert result["groupid"] == group_id
    assert result["role"] == "arn:aws:iam::828416469395:role/Tier1_Support"


def test_saml_with_custom_regex():
    group_name = "AWS_123456789123_developer"
    group_id = "groupid"
    custom_regex = "AWS_(?{{accountid}}\\d+)_(?{{role}}[a-zA-Z0-9+=,.@\\-_]+)"

    result = transform_okta_group_to_aws_role(group_id, group_name, custom_regex)

    assert result
    assert result["groupid"] == group_id
    assert result["role"] == "arn:aws:iam::123456789123:role/developer"


def test_parse_okta_group_name() -> None:
    group_name = 'AWS_1234_myrole1'
    mapping_regex = r"AWS_(?{{accountid}}\d+)_(?{{role}}[a-zA-Z0-9+=,.@\-_]+)"

    # Act
    account_role: Optional[AccountRole] = _parse_okta_group_name(group_name, mapping_regex)

    # Assert
    assert account_role is not None
    assert account_role.role_name == 'myrole1'
    assert account_role.account_id == '1234'


@mock.patch.object(
    cartography.intel.okta.awssaml,
    'get_awssso_role_arn',
    side_effect=[
        'arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef',
        'arn:aws:iam:1234:role/AWSReservedSSO_myrole2_bcdefa',
        'arn:aws:iam:1234:role/AWSReservedSSO_myrole3_cdefab',
    ],
)
def test_query_for_okta_to_awssso_role_mapping(mock_get_awssso_role_arn: MagicMock) -> None:
    # Arrange
    neo4j_session = mock.MagicMock()
    mapping_regex = r"AWS_(?{{accountid}}\d+)_(?{{role}}[a-zA-Z0-9+=,.@\-_]+)"
    okta_groups = [
        OktaGroup(group_id='0oaxm1', group_name='AWS_1234_myrole1'),
        OktaGroup(group_id='0oaxm2', group_name='AWS_1234_myrole2'),
        OktaGroup(group_id='0oaxm3', group_name='AWS_1234_myrole3'),
    ]

    # Act
    result = query_for_okta_to_awssso_role_mapping(neo4j_session, okta_groups, mapping_regex)

    # Assert
    assert result == [
        GroupRole(okta_group_id='0oaxm1', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef'),
        GroupRole(okta_group_id='0oaxm2', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole2_bcdefa'),
        GroupRole(okta_group_id='0oaxm3', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole3_cdefab'),
    ]
