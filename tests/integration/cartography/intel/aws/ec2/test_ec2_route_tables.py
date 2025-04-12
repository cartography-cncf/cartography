from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.route_tables
from cartography.intel.aws.ec2.route_tables import sync_route_tables
from tests.data.aws.ec2.route_tables import DESCRIBE_ROUTE_TABLES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789

@patch.object(
    cartography.intel.aws.ec2.route_tables,
    'get_route_tables',
    return_value=DESCRIBE_ROUTE_TABLES['RouteTables'],
)
def test_sync_route_tables(mock_get_route_tables, neo4j_session):
    """
    Ensure that route tables, routes, and associations get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_route_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert route tables exist
    assert check_nodes(neo4j_session, 'EC2RouteTable', ['id', 'route_table_id']) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb"),
    }

    # Assert route table associations exist
    assert check_nodes(neo4j_session, 'EC2RouteTableAssociation', ['id', 'route_table_association_id']) == {
        ("rtbassoc-aaaaaaaaaaaaaaaaa", "rtbassoc-aaaaaaaaaaaaaaaaa"),
        ("rtbassoc-bbbbbbbbbbbbbbbbb", "rtbassoc-bbbbbbbbbbbbbbbbb"),
        ("rtbassoc-ccccccccccccccccc", "rtbassoc-ccccccccccccccccc"),
    }

    # Assert routes exist
    assert check_nodes(neo4j_session, 'EC2Route', ['id', 'route_id']) == {
        ("rtb-aaaaaaaaaaaaaaaaa-172.31.0.0/16-", "rtb-aaaaaaaaaaaaaaaaa-172.31.0.0/16-"),
        ("rtb-aaaaaaaaaaaaaaaaa-0.0.0.0/0-", "rtb-aaaaaaaaaaaaaaaaa-0.0.0.0/0-"),
        ("rtb-bbbbbbbbbbbbbbbbb-10.1.0.0/16-", "rtb-bbbbbbbbbbbbbbbbb-10.1.0.0/16-"),
        ("rtb-bbbbbbbbbbbbbbbbb-0.0.0.0/0-", "rtb-bbbbbbbbbbbbbbbbb-0.0.0.0/0-"),
    }

    # Assert route table to VPC relationships
    assert check_rels(
        neo4j_session,
        'EC2RouteTable',
        'id',
        'AWSVpc',
        'id',
        'MEMBER_OF_VPC',
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "vpc-aaaaaaaaaaaaaaaaa"),
        ("rtb-bbbbbbbbbbbbbbbbb", "vpc-bbbbbbbbbbbbbbbbb"),
    }

    # Assert route table to route relationships
    assert check_rels(
        neo4j_session,
        'EC2RouteTable',
        'id',
        'EC2Route',
        'id',
        'CONTAINS',
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa-172.31.0.0/16-"),
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa-0.0.0.0/0-"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb-10.1.0.0/16-"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb-0.0.0.0/0-"),
    }

    # Assert route table to association relationships
    assert check_rels(
        neo4j_session,
        'EC2RouteTable',
        'id',
        'EC2RouteTableAssociation',
        'id',
        'HAS_ASSOCIATION',
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtbassoc-aaaaaaaaaaaaaaaaa"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtbassoc-bbbbbbbbbbbbbbbbb"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtbassoc-ccccccccccccccccc"),
    }

    # Assert route table to AWS account relationships
    assert check_rels(
        neo4j_session,
        'EC2RouteTable',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb", TEST_ACCOUNT_ID),
    }

    # Assert route to AWS account relationships
    assert check_rels(
        neo4j_session,
        'EC2Route',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa-172.31.0.0/16-", TEST_ACCOUNT_ID),
        ("rtb-aaaaaaaaaaaaaaaaa-0.0.0.0/0-", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb-10.1.0.0/16-", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb-0.0.0.0/0-", TEST_ACCOUNT_ID),
    }

    # Assert route table association to AWS account relationships
    assert check_rels(
        neo4j_session,
        'EC2RouteTableAssociation',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ("rtbassoc-aaaaaaaaaaaaaaaaa", TEST_ACCOUNT_ID),
        ("rtbassoc-bbbbbbbbbbbbbbbbb", TEST_ACCOUNT_ID),
        ("rtbassoc-ccccccccccccccccc", TEST_ACCOUNT_ID),
    }
