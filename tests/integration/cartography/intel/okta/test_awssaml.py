from cartography.intel.okta.awssaml import _load_okta_group_to_awssso_roles
from cartography.intel.okta.awssaml import get_awssso_okta_groups
from cartography.intel.okta.awssaml import get_awssso_role_arn
from cartography.intel.okta.awssaml import GroupRole
from cartography.intel.okta.awssaml import OktaGroup
from tests.integration.util import check_rels


TEST_UPDATE_TAG = 000000
TEST_ORG_ID = 'ORG_ID'
DEFAULT_REGEX = r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$"


def test_get_awssso_okta_groups(neo4j_session):
    # Arrange
    _ensure_okta_test_data(neo4j_session)

    # Act
    groups = get_awssso_okta_groups(neo4j_session, TEST_ORG_ID)

    # Assert that the data objects are created correctly
    assert sorted(groups) == [
        OktaGroup(group_id='0oaxm1', group_name='AWS_1234_myrole1'),
        OktaGroup(group_id='0oaxm2', group_name='AWS_1234_myrole2'),
        OktaGroup(group_id='0oaxm3', group_name='AWS_1234_myrole3'),
    ]


def _ensure_okta_test_data(neo4j_session):
    test_groups = [
        ('AWS_1234_myrole1', '0oaxm1'),
        ('AWS_1234_myrole2', '0oaxm2'),
        ('AWS_1234_myrole3', '0oaxm3'),
    ]
    for group in test_groups:
        neo4j_session.run(
            '''
            MERGE (o:OktaOrganization{id: $ORG_ID})
            MERGE (o)-[:RESOURCE]-> (g:OktaGroup{name: $GROUP_NAME, id: $GROUP_ID, lastupdated: $UPDATE_TAG})
            MERGE (o)-[:RESOURCE]->(a:OktaApplication{name:"amazon_aws_sso"})
            MERGE (a)<-[:APPLICATION]-(g)
            ''',
            ORG_ID=TEST_ORG_ID,
            GROUP_NAME=group[0],
            GROUP_ID=group[1],
            UPDATE_TAG=TEST_UPDATE_TAG,
        )


def test_get_awssso_role_arn(neo4j_session):
    # Arrange
    _ensure_aws_test_data(neo4j_session)

    # Act and assert
    assert get_awssso_role_arn(
        '1234',
        'myrole1',
        neo4j_session,
    ) == 'arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef'

    # Act and assert that we grab the role in the other account correctly
    assert get_awssso_role_arn(
        '2345',
        'myrole1',
        neo4j_session,
    ) == 'arn:aws:iam:2345:role/AWSReservedSSO_myrole1_abcdef'

    # Act and assert the None case
    assert get_awssso_role_arn('1234', 'myrole4', neo4j_session) is None


def _ensure_aws_test_data(neo4j_session):
    # Arrange
    test_sso_roles = [
        ('AWSReservedSSO_myrole1_abcdef', 'arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef', '1234'),
        ('AWSReservedSSO_myrole2_bcdefa', 'arn:aws:iam:1234:role/AWSReservedSSO_myrole2_bcdefa', '1234'),
        ('AWSReservedSSO_myrole3_cdefab', 'arn:aws:iam:1234:role/AWSReservedSSO_myrole3_cdefab', '1234'),
        # Add one that has same role name but is in a different account. Expect this to not be returned.
        ('AWSReservedSSO_myrole1_abcdef', 'arn:aws:iam:2345:role/AWSReservedSSO_myrole1_abcdef', '2345'),
    ]
    for role in test_sso_roles:
        neo4j_session.run(
            '''
            MERGE (o:AWSAccount{id: $account_id})
            MERGE (o)-[:RESOURCE]->
                  (r1:AWSRole{name: $role_name, id: $arn, arn: $arn, path: $path, lastupdated: $update_tag})
            ''',
            role_name=role[0],
            arn=role[1],
            id=role[1],
            account_id=role[2],
            path='/aws-reserved/sso.amazonaws.com/',
            update_tag=TEST_UPDATE_TAG,
        )


def test_load_okta_group_to_awssso_roles(neo4j_session):
    # Arrange
    _ensure_aws_test_data(neo4j_session)
    _ensure_okta_test_data(neo4j_session)
    group_roles = [
        GroupRole(okta_group_id='0oaxm1', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef'),
        GroupRole(okta_group_id='0oaxm2', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole2_bcdefa'),
        GroupRole(okta_group_id='0oaxm3', aws_role_arn='arn:aws:iam:1234:role/AWSReservedSSO_myrole3_cdefab'),
    ]

    # Act
    _load_okta_group_to_awssso_roles(neo4j_session, group_roles, TEST_UPDATE_TAG)

    # Assert
    assert check_rels(
        neo4j_session,
        'AWSRole',
        'id',
        'OktaGroup',
        'name',
        'ALLOWED_BY',
        False,
    ) == {
        ('arn:aws:iam:1234:role/AWSReservedSSO_myrole1_abcdef', 'AWS_1234_myrole1'),
        ('arn:aws:iam:1234:role/AWSReservedSSO_myrole2_bcdefa', 'AWS_1234_myrole2'),
        ('arn:aws:iam:1234:role/AWSReservedSSO_myrole3_cdefab', 'AWS_1234_myrole3'),
    }
