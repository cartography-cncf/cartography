from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.elastic_ip_addresses
import cartography.intel.aws.ec2.nat_gateways
import cartography.intel.aws.ec2.subnets
import cartography.intel.aws.ec2.vpc
from cartography.intel.aws.ec2.elastic_ip_addresses import sync_elastic_ip_addresses
from cartography.intel.aws.ec2.nat_gateways import sync_nat_gateways
from cartography.intel.aws.ec2.subnets import sync_subnets
from cartography.intel.aws.ec2.vpc import sync_vpc
from tests.data.aws.ec2.elastic_ip_addresses import GET_ELASTIC_IP_ADDRESSES
from tests.data.aws.ec2.nat_gateways import TEST_NAT_GATEWAYS
from tests.data.aws.ec2.subnets import DESCRIBE_SUBNETS
from tests.data.aws.ec2.vpcs import TEST_VPCS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
TEST_UPDATE_TAG = 123456789


def _setup_prerequisites(neo4j_session, boto3_session):
    """Create VPC, Subnet, and ElasticIPAddress nodes as prerequisites."""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync_vpc(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_subnets(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_elastic_ip_addresses(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )


@patch.object(
    cartography.intel.aws.ec2.vpc,
    "get_ec2_vpcs",
    return_value=TEST_VPCS,
)
@patch.object(
    cartography.intel.aws.ec2.subnets,
    "get_subnet_data",
    return_value=DESCRIBE_SUBNETS,
)
@patch.object(
    cartography.intel.aws.ec2.elastic_ip_addresses,
    "get_elastic_ip_addresses",
    return_value=GET_ELASTIC_IP_ADDRESSES,
)
@patch.object(
    cartography.intel.aws.ec2.nat_gateways,
    "get_nat_gateways",
    return_value=TEST_NAT_GATEWAYS,
)
def test_sync_nat_gateways(
    mock_get_ngw,
    mock_get_eip,
    mock_get_subnets,
    mock_get_vpcs,
    neo4j_session,
):
    """
    Ensure that NAT gateways are loaded with correct properties and all relationships.
    """
    boto3_session = MagicMock()
    _setup_prerequisites(neo4j_session, boto3_session)

    sync_nat_gateways(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert NAT Gateway nodes exist with correct properties
    assert check_nodes(neo4j_session, "AWSNatGateway", ["id", "arn"]) == {
        (
            "nat-0abc1234567890001",
            f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT_ID}:natgateway/nat-0abc1234567890001",
        ),
        (
            "nat-0def1234567890002",
            f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT_ID}:natgateway/nat-0def1234567890002",
        ),
        (
            "nat-0prv1234567890003",
            f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT_ID}:natgateway/nat-0prv1234567890003",
        ),
    }

    # Assert RESOURCE relationship to AWSAccount
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSNatGateway",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "nat-0abc1234567890001"),
        (TEST_ACCOUNT_ID, "nat-0def1234567890002"),
        (TEST_ACCOUNT_ID, "nat-0prv1234567890003"),
    }

    # Assert ATTACHED_TO relationship to AWSVpc
    assert check_rels(
        neo4j_session,
        "AWSNatGateway",
        "id",
        "AWSVpc",
        "id",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        ("nat-0abc1234567890001", "vpc-025873e026b9e8ee6"),
        ("nat-0def1234567890002", "vpc-025873e026b9e8ee6"),
        ("nat-0prv1234567890003", "vpc-05326141848d1c681"),
    }

    # Assert PART_OF_SUBNET relationship to EC2Subnet
    assert check_rels(
        neo4j_session,
        "AWSNatGateway",
        "id",
        "EC2Subnet",
        "id",
        "PART_OF_SUBNET",
        rel_direction_right=True,
    ) == {
        ("nat-0abc1234567890001", "subnet-0773409557644dca4"),
        ("nat-0def1234567890002", "subnet-020b2f3928f190ce8"),
        ("nat-0prv1234567890003", "subnet-0fa9c8fa7cb241479"),
    }

    # Assert ASSOCIATED_WITH relationship to ElasticIPAddress
    # Only nat-0abc1234567890001 has an EIP that exists in test data
    assert check_rels(
        neo4j_session,
        "AWSNatGateway",
        "id",
        "ElasticIPAddress",
        "allocation_id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("nat-0abc1234567890001", "eipalloc-00000000000000000"),
        ("nat-0abc1234567890001", "eipalloc-11111111111111111"),
    }
