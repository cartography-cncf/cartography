from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.vpc
from cartography.intel.aws.ec2.vpc import sync_vpc
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
def test_sync_vpc(mock_get_vpcs, neo4j_session):
    """
    Ensure that VPCs actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_vpc(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert VPCs exist with correct properties
    assert check_nodes(
        neo4j_session, "AWSVpc", ["id", "primary_cidr_block", "is_default"]
    ) == {
        ("vpc-038cf", "172.31.0.0/16", True),
        ("vpc-0f510", "10.1.0.0/16", False),
    }

    # Assert VPCs are connected to AWS Account
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSVpc",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("12345", "vpc-038cf"),
        ("12345", "vpc-0f510"),
    }

    # Assert CIDR blocks are properly associated with VPCs
    assert check_rels(
        neo4j_session,
        "AWSVpc",
        "id",
        "AWSCidrBlock",
        "id",
        "BLOCK_ASSOCIATION",
        rel_direction_right=True,
    ) == {
        ("vpc-038cf", "vpc-038cf|172.31.0.0/16"),
        ("vpc-0f510", "vpc-0f510|10.1.0.0/16"),
    }

    # Assert CIDR blocks have correct properties
    assert check_nodes(
        neo4j_session,
        "AWSCidrBlock",
        ["id", "cidr_block", "association_id", "block_state"],
    ) == {
        (
            "vpc-038cf|172.31.0.0/16",
            "172.31.0.0/16",
            "vpc-cidr-assoc-0daea",
            "associated",
        ),
        ("vpc-0f510|10.1.0.0/16", "10.1.0.0/16", "vpc-cidr-assoc-087ee", "associated"),
    }
