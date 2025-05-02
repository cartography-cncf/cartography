from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.route_tables
from cartography.intel.aws.ec2.internet_gateways import sync_internet_gateways
from cartography.intel.aws.ec2.route_tables import sync_route_tables
from cartography.intel.aws.ec2.subnets import load_subnets
from cartography.intel.aws.ec2.vpc import sync_vpc
from tests.data.aws.ec2.internet_gateways import TEST_INTERNET_GATEWAYS
from tests.data.aws.ec2.route_tables import DESCRIBE_ROUTE_TABLES
from tests.data.aws.ec2.subnets import DESCRIBE_SUBNETS
from tests.data.aws.ec2.vpcs import TEST_VPCS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_fake_subnets(neo4j_session):
    load_subnets(
        neo4j_session,
        DESCRIBE_SUBNETS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.ec2.vpc,
    "get_ec2_vpcs",
    return_value=TEST_VPCS,
)
@patch.object(
    cartography.intel.aws.ec2.internet_gateways,
    "get_internet_gateways",
    return_value=TEST_INTERNET_GATEWAYS,
)
@patch.object(
    cartography.intel.aws.ec2.route_tables,
    "get_route_tables",
    return_value=DESCRIBE_ROUTE_TABLES["RouteTables"],
)
def test_sync_route_tables(
    mock_get_vpcs, mock_get_gateways, mock_get_route_tables, neo4j_session
):
    """
    Ensure that route tables, routes, and associations get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_fake_subnets(neo4j_session)
    # Add in fake VPC data
    sync_vpc(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    # Add in fake internet gateway data
    sync_internet_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act
    sync_route_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert route tables exist
    assert check_nodes(neo4j_session, "EC2RouteTable", ["id", "route_table_id"]) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb"),
    }

    # Assert route table associations exist
    assert check_nodes(
        neo4j_session, "EC2RouteTableAssociation", ["id", "route_table_association_id"]
    ) == {
        ("rtbassoc-aaaaaaaaaaaaaaaaa", "rtbassoc-aaaaaaaaaaaaaaaaa"),
        ("rtbassoc-bbbbbbbbbbbbbbbbb", "rtbassoc-bbbbbbbbbbbbbbbbb"),
        ("rtbassoc-ccccccccccccccccc", "rtbassoc-ccccccccccccccccc"),
        ("rtbassoc-ddddddddddddddddd", "rtbassoc-ddddddddddddddddd"),
    }

    # Assert routes exist
    assert check_nodes(neo4j_session, "EC2Route", ["id"]) == {
        ("rtb-aaaaaaaaaaaaaaaaa|172.31.0.0/16",),
        ("rtb-aaaaaaaaaaaaaaaaa|0.0.0.0/0",),
        ("rtb-bbbbbbbbbbbbbbbbb|10.1.0.0/16",),
        ("rtb-bbbbbbbbbbbbbbbbb|0.0.0.0/0",),
    }

    # Assert route table to route relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTable",
        "id",
        "EC2Route",
        "id",
        "ROUTE",
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa|172.31.0.0/16"),
        ("rtb-aaaaaaaaaaaaaaaaa", "rtb-aaaaaaaaaaaaaaaaa|0.0.0.0/0"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb|10.1.0.0/16"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtb-bbbbbbbbbbbbbbbbb|0.0.0.0/0"),
    }

    # Assert route table to association relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTable",
        "id",
        "EC2RouteTableAssociation",
        "id",
        "ASSOCIATION",
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "rtbassoc-aaaaaaaaaaaaaaaaa"),
        ("rtb-aaaaaaaaaaaaaaaaa", "rtbassoc-ddddddddddddddddd"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtbassoc-bbbbbbbbbbbbbbbbb"),
        ("rtb-bbbbbbbbbbbbbbbbb", "rtbassoc-ccccccccccccccccc"),
    }

    # Assert route table to AWS account relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTable",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb", TEST_ACCOUNT_ID),
    }

    # Assert route to AWS account relationships
    assert check_rels(
        neo4j_session,
        "EC2Route",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa|172.31.0.0/16", TEST_ACCOUNT_ID),
        ("rtb-aaaaaaaaaaaaaaaaa|0.0.0.0/0", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb|10.1.0.0/16", TEST_ACCOUNT_ID),
        ("rtb-bbbbbbbbbbbbbbbbb|0.0.0.0/0", TEST_ACCOUNT_ID),
    }

    # Assert route table association to AWS account relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTableAssociation",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("rtbassoc-aaaaaaaaaaaaaaaaa", TEST_ACCOUNT_ID),
        ("rtbassoc-bbbbbbbbbbbbbbbbb", TEST_ACCOUNT_ID),
        ("rtbassoc-ccccccccccccccccc", TEST_ACCOUNT_ID),
        ("rtbassoc-ddddddddddddddddd", TEST_ACCOUNT_ID),
    }

    # Assert route table association to subnet relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTableAssociation",
        "id",
        "EC2Subnet",
        "subnetid",
        "ASSOCIATED_SUBNET",
        rel_direction_right=True,
    ) == {
        ("rtbassoc-bbbbbbbbbbbbbbbbb", "subnet-0773409557644dca4"),
        ("rtbassoc-ccccccccccccccccc", "subnet-0fa9c8fa7cb241479"),
    }
    # Assert route table to VPC relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTable",
        "id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa", "vpc-038cf"),
        ("rtb-bbbbbbbbbbbbbbbbb", "vpc-0f510"),
    }

    # Assert route table associations to internet gateway relationships
    assert check_rels(
        neo4j_session,
        "EC2RouteTableAssociation",
        "id",
        "AWSInternetGateway",
        "id",
        "ASSOCIATED_IGW_FOR_INGRESS",
        rel_direction_right=True,
    ) == {
        ("rtbassoc-ddddddddddddddddd", "igw-013cb"),
    }

    # Assert route table to internet gateway relationships
    assert check_rels(
        neo4j_session,
        "EC2Route",
        "id",
        "AWSInternetGateway",
        "id",
        "ROUTES_TO_GATEWAY",
        rel_direction_right=True,
    ) == {
        ("rtb-aaaaaaaaaaaaaaaaa|0.0.0.0/0", "igw-0387"),
        ("rtb-bbbbbbbbbbbbbbbbb|0.0.0.0/0", "igw-0387"),
    }
