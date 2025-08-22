from unittest.mock import MagicMock
from unittest.mock import patch

import cartography
from cartography.intel.aws.ec2.network_acls import sync_network_acls
from cartography.intel.aws.ec2.route_tables import sync_route_tables
from cartography.intel.aws.ec2.security_groups import sync_ec2_security_groupinfo
from cartography.intel.aws.ec2.subnets import sync_subnets
from cartography.intel.aws.ec2.vpc import sync_vpc
from cartography.intel.aws.ec2.vpc_peerings import sync_vpc_peerings
from cartography.intel.aws.redshift import sync as sync_redshift
from tests.data.aws.ec2.network_acls.network_acls import DESCRIBE_NETWORK_ACLS
from tests.data.aws.ec2.route_tables import DESCRIBE_ROUTE_TABLES
from tests.data.aws.ec2.security_groups import DESCRIBE_SGS
from tests.data.aws.ec2.subnets import DESCRIBE_SUBNETS
from tests.data.aws.ec2.vpc_peerings import DESCRIBE_VPC_PEERINGS
from tests.data.aws.ec2.vpcs import TEST_VPCS
from tests.data.aws.redshift import CLUSTERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "12345"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.redshift,
    "get_redshift_cluster_data",
    return_value=CLUSTERS,
)
@patch.object(
    cartography.intel.aws.ec2.vpc_peerings,
    "get_vpc_peerings_data",
    return_value=DESCRIBE_VPC_PEERINGS,
)
@patch.object(
    cartography.intel.aws.ec2.route_tables,
    "get_route_tables",
    return_value=DESCRIBE_ROUTE_TABLES["RouteTables"],
)
@patch.object(
    cartography.intel.aws.ec2.security_groups,
    "get_ec2_security_group_data",
    return_value=DESCRIBE_SGS,
)
@patch.object(
    cartography.intel.aws.ec2.network_acls,
    "get_network_acl_data",
    return_value=DESCRIBE_NETWORK_ACLS,
)
@patch.object(
    cartography.intel.aws.ec2.subnets,
    "get_subnet_data",
    return_value=DESCRIBE_SUBNETS,
)
@patch.object(
    cartography.intel.aws.ec2.vpc,
    "get_ec2_vpcs",
    return_value=TEST_VPCS,
)
def test_sync_vpc(
    mock_get_vpcs,
    mock_get_subnets,
    mock_get_acls,
    mock_get_sgs,
    mock_get_route_tables,
    mock_get_peerings,
    mock_get_redshift,
    neo4j_session,
):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act - Sync VPCs first, then other resources that reference them
    sync_vpc(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_ec2_security_groupinfo(
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

    sync_network_acls(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_route_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_vpc_peerings(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_redshift(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert : Check Nodes from here

    # Assert VPCs exist with correct properties
    assert check_nodes(
        neo4j_session, "AWSVpc", ["id", "primary_cidr_block", "is_default"]
    ) == {
        ("vpc-038cf", "172.31.0.0/16", True),
        ("vpc-0f510", "10.1.0.0/16", False),
        ("vpc-0a1b2", "2001:db8::/32", False),
        ("vpc-05326141848d1c681", "10.0.0.0/16", False),
        ("vpc-0767", "192.168.0.0/16", False),
        ("vpc-025873e026b9e8ee6", "172.16.0.0/16", False),
        ("vpc-0015dc961e537676a", None, None),  # VPC Created by VPC peering
        ("vpc-055d355d6d2e498fa", None, None),  # VPC Created by VPC peering
        ("my_vpc", None, None),  # VPC Created by Redshift
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
        (
            "vpc-0a1b2|2001:db8::/32",
            "2001:db8::/32",
            "vpc-ipv6-cidr-assoc-0a1b2",
            "associated",
        ),
        (
            "vpc-05326141848d1c681|10.0.0.0/16",
            "10.0.0.0/16",
            "vpc-cidr-assoc-security-groups",
            "associated",
        ),
        (
            "vpc-0767|192.168.0.0/16",
            "192.168.0.0/16",
            "vpc-cidr-assoc-network-acls",
            "associated",
        ),
        (
            "vpc-025873e026b9e8ee6|172.16.0.0/16",
            "172.16.0.0/16",
            "vpc-cidr-assoc-subnets",
            "associated",
        ),
        (
            "vpc-0015dc961e537676a|10.0.0.0/16",
            "10.0.0.0/16",
            None,  # Created by VPC peering
            None,
        ),
        (
            "vpc-055d355d6d2e498fa|10.1.0.0/16",
            "10.1.0.0/16",
            None,  # Created by VPC peering
            None,
        ),
    }

    # Assert AWSIPv4CIDR blocks have correct properties
    assert check_nodes(
        neo4j_session,
        "AWSIpv4CidrBlock",
        ["id", "cidr_block", "association_id", "block_state"],
    ) == {
        (
            "vpc-038cf|172.31.0.0/16",
            "172.31.0.0/16",
            "vpc-cidr-assoc-0daea",
            "associated",
        ),
        ("vpc-0f510|10.1.0.0/16", "10.1.0.0/16", "vpc-cidr-assoc-087ee", "associated"),
        (
            "vpc-05326141848d1c681|10.0.0.0/16",
            "10.0.0.0/16",
            "vpc-cidr-assoc-security-groups",
            "associated",
        ),
        (
            "vpc-0767|192.168.0.0/16",
            "192.168.0.0/16",
            "vpc-cidr-assoc-network-acls",
            "associated",
        ),
        (
            "vpc-025873e026b9e8ee6|172.16.0.0/16",
            "172.16.0.0/16",
            "vpc-cidr-assoc-subnets",
            "associated",
        ),
        (
            "vpc-0015dc961e537676a|10.0.0.0/16",
            "10.0.0.0/16",
            None,  # Created by VPC peering
            None,
        ),
        (
            "vpc-055d355d6d2e498fa|10.1.0.0/16",
            "10.1.0.0/16",
            None,  # Created by VPC peering
            None,
        ),
    }

    # Assert AWSIPv6CIDR blocks have correct properties
    assert check_nodes(
        neo4j_session,
        "AWSIpv6CidrBlock",
        ["id", "cidr_block", "association_id", "block_state"],
    ) == {
        (
            "vpc-0a1b2|2001:db8::/32",
            "2001:db8::/32",
            "vpc-ipv6-cidr-assoc-0a1b2",
            "associated",
        ),
    }

    # Assert : Check Relations from here

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
        ("12345", "vpc-0a1b2"),
        ("12345", "vpc-05326141848d1c681"),
        ("12345", "vpc-0767"),
        ("12345", "vpc-025873e026b9e8ee6"),
        ("000000000000", "vpc-0015dc961e537676a"),  # AWS Account Created by VPC peering
        ("000000000000", "vpc-055d355d6d2e498fa"),  # AWS Account Created by VPC peering
        #    ("1111", "my_vpc"), # AWS Account not Created by Redshift
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
        ("vpc-0a1b2", "vpc-0a1b2|2001:db8::/32"),
        ("vpc-05326141848d1c681", "vpc-05326141848d1c681|10.0.0.0/16"),
        ("vpc-0767", "vpc-0767|192.168.0.0/16"),
        ("vpc-025873e026b9e8ee6", "vpc-025873e026b9e8ee6|172.16.0.0/16"),
        (
            "vpc-0015dc961e537676a",
            "vpc-0015dc961e537676a|10.0.0.0/16",
        ),  # Associated with VPC peering
        (
            "vpc-055d355d6d2e498fa",
            "vpc-055d355d6d2e498fa|10.1.0.0/16",
        ),  # Associated with VPC peering
        # ("my_vpc", "my_vpc|10.0.0.0/16"), # Not Created or Associated with Redshift
    }

    # Assert subnets are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "EC2Subnet",
        "subnetid",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        ("subnet-0773409557644dca4", "vpc-025873e026b9e8ee6"),
        ("subnet-020b2f3928f190ce8", "vpc-025873e026b9e8ee6"),
        ("subnet-0fa9c8fa7cb241479", "vpc-05326141848d1c681"),
    }

    # Assert network ACLs are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "EC2NetworkAcl",
        "network_acl_id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        ("acl-077e", "vpc-0767"),
    }

    # Assert security groups are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "EC2SecurityGroup",
        "id",
        "AWSVpc",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=False,
    ) == {
        (
            "sg-web-server-12345",
            "vpc-05326141848d1c681",
        ),  # Security groups test data contains 5 different security groups
        (
            "sg-0fd4fff275d63600f",
            "vpc-05326141848d1c681",
        ),  # All created at the time of running sync
        ("sg-028e2522c72719996", "vpc-05326141848d1c681"),
        ("sg-06c795c66be8937be", "vpc-025873e026b9e8ee6"),
        ("sg-053dba35430032a0d", "vpc-025873e026b9e8ee6"),
    }

    # Assert route tables are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "EC2RouteTable",
        "route_table_id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        (
            "rtb-aaaaaaaaaaaaaaaaa",
            "vpc-038cf",
        ),  # Route tables test data contains 2 different route tables
        ("rtb-bbbbbbbbbbbbbbbbb", "vpc-0f510"),
    }

    # Assert VPC peering connections are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "AWSPeeringConnection",
        "id",
        "AWSVpc",
        "id",
        "REQUESTER_VPC",
        rel_direction_right=True,
    ) == {
        (
            "pcx-09969456d9ec69ab6",
            "vpc-055d355d6d2e498fa",
        ),  # AWSVpc created by VPC_peering sync,VPC peering test data contains 1 requester VPC peering
    }

    assert check_rels(
        neo4j_session,
        "AWSPeeringConnection",
        "id",
        "AWSVpc",
        "id",
        "ACCEPTER_VPC",
        rel_direction_right=True,
    ) == {
        (
            "pcx-09969456d9ec69ab6",
            "vpc-0015dc961e537676a",
        ),  # AWSVpc created by VPC_peering sync, VPC peering test data contains 1 accepter VPC peering
    }

    # Assert Redshift clusters are connected to their VPCs
    assert check_rels(
        neo4j_session,
        "RedshiftCluster",
        "id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:redshift:us-east-1:12345:cluster:my-cluster",
            "my_vpc",
        ),  # AWSVpc created by RedshiftCluster sync,  Redshift cluster has a special way of assigning arn
    }  # it takes the region, account id, and cluster name and creates an arn -> thats why it maches this test

    # Assert VPC peering connections are connected to their requester CIDR blocks
    assert check_rels(
        neo4j_session,
        "AWSPeeringConnection",
        "id",
        "AWSCidrBlock",
        "id",
        "REQUESTER_CIDR",
        rel_direction_right=True,
    ) == {
        (
            "pcx-09969456d9ec69ab6",
            "vpc-055d355d6d2e498fa|10.1.0.0/16",
        ),  # Requester CIDR block for VPC peering
    }

    # Assert VPC peering connections are connected to their accepter CIDR blocks
    assert check_rels(
        neo4j_session,
        "AWSPeeringConnection",
        "id",
        "AWSCidrBlock",
        "id",
        "ACCEPTER_CIDR",
        rel_direction_right=True,
    ) == {
        (
            "pcx-09969456d9ec69ab6",
            "vpc-0015dc961e537676a|10.0.0.0/16",
        ),  # Accepter CIDR block for VPC peering
    }
