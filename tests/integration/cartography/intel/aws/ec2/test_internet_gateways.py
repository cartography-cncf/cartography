from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.internet_gateways
from cartography.intel.aws.ec2.internet_gateways import sync_internet_gateways
from cartography.intel.aws.ec2.vpc import sync_vpc
from tests.data.aws.ec2.internet_gateways import TEST_INTERNET_GATEWAYS
from tests.data.aws.ec2.vpcs import TEST_VPCS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "12345"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


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
def test_sync_internet_gateways(mock_get_vpcs, mock_get_gateways, neo4j_session):
    """
    Ensure that internet gateways actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    # Add in fake VPC data for igw to be attached to
    sync_vpc(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act
    sync_internet_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert Internet Gateways exist
    assert check_nodes(neo4j_session, "AWSInternetGateway", ["id", "arn"]) == {
        ("igw-013cb", "arn:aws:ec2:us-east-1:12345:internet-gateway/igw-013cb"),
        ("igw-0387", "arn:aws:ec2:us-east-1:12345:internet-gateway/igw-0387"),
    }

    # Assert Internet Gateways are connected to AWS Account
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInternetGateway",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("12345", "igw-013cb"),
        ("12345", "igw-0387"),
    }

    # Assert Internet Gateways are connected to VPCs
    assert check_rels(
        neo4j_session,
        "AWSInternetGateway",
        "id",
        "AWSVpc",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        ("igw-013cb", "vpc-038cf"),
        ("igw-0387", "vpc-0f510"),
    }
