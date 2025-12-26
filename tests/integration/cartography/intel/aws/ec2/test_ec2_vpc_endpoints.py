from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.vpc_endpoint
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoints
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_route_table_relationships
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_security_group_relationships
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_subnet_relationships
from cartography.intel.aws.ec2.vpc_endpoint import sync_vpc_endpoints
from cartography.intel.aws.ec2.vpc_endpoint import transform_vpc_endpoint_data
from tests.data.aws.ec2.vpc_endpoints import DESCRIBE_VPC_ENDPOINTS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_vpc_endpoints(neo4j_session):
    """Test that VPC endpoints are loaded correctly"""
    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert that VPC endpoint nodes are created
    assert check_nodes(
        neo4j_session,
        "AWSVpcEndpoint",
        ["vpc_endpoint_id", "vpc_endpoint_type", "state"]
    ) == {
        ("vpce-1234567890abcdef0", "Interface", "available"),
        ("vpce-gateway123", "Gateway", "available"),
        ("vpce-gwlb456", "GatewayLoadBalancer", "available"),
    }


def test_load_vpc_endpoint_to_account_relationship(neo4j_session):
    """Test that VPC endpoints are linked to AWS accounts"""
    # Create test AWS account
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert VPC endpoints are connected to AWS account
    assert check_rels(
        neo4j_session,
        "AWSVpcEndpoint",
        "vpc_endpoint_id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("vpce-1234567890abcdef0", TEST_ACCOUNT_ID),
        ("vpce-gateway123", TEST_ACCOUNT_ID),
        ("vpce-gwlb456", TEST_ACCOUNT_ID),
    }


def test_load_vpc_endpoint_to_vpc_relationship(neo4j_session):
    """Test that VPC endpoints are linked to VPCs"""
    # Create test VPCs
    neo4j_session.run(
        """
        MERGE (vpc1:AWSVpc{id: 'vpc-12345678'})
        ON CREATE SET vpc1.firstseen = timestamp()
        SET vpc1.lastupdated = $update_tag

        MERGE (vpc2:AWSVpc{id: 'vpc-87654321'})
        ON CREATE SET vpc2.firstseen = timestamp()
        SET vpc2.lastupdated = $update_tag

        MERGE (vpc3:AWSVpc{id: 'vpc-11111111'})
        ON CREATE SET vpc3.firstseen = timestamp()
        SET vpc3.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert VPC endpoints are connected to VPCs
    assert check_rels(
        neo4j_session,
        "AWSVpcEndpoint",
        "vpc_endpoint_id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
    ) == {
        ("vpce-1234567890abcdef0", "vpc-12345678"),
        ("vpce-gateway123", "vpc-87654321"),
        ("vpce-gwlb456", "vpc-11111111"),
    }


def test_load_vpc_endpoint_subnet_relationships(neo4j_session):
    """Test that interface and gateway load balancer VPC endpoints are linked to subnets"""
    # Create test subnets
    neo4j_session.run(
        """
        MERGE (subnet1:EC2Subnet{subnetid: 'subnet-12345'})
        ON CREATE SET subnet1.firstseen = timestamp()
        SET subnet1.lastupdated = $update_tag

        MERGE (subnet2:EC2Subnet{subnetid: 'subnet-67890'})
        ON CREATE SET subnet2.firstseen = timestamp()
        SET subnet2.lastupdated = $update_tag

        MERGE (subnet3:EC2Subnet{subnetid: 'subnet-gwlb-1'})
        ON CREATE SET subnet3.firstseen = timestamp()
        SET subnet3.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_subnet_relationships(
        neo4j_session,
        transformed_data,
        TEST_UPDATE_TAG,
    )

    # Interface and GatewayLoadBalancer endpoints should have subnet relationships
    expected_rels = {
        ("vpce-1234567890abcdef0", "subnet-12345"),
        ("vpce-1234567890abcdef0", "subnet-67890"),
        ("vpce-gwlb456", "subnet-gwlb-1"),
    }

    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint)-[:USES_SUBNET]->(subnet:EC2Subnet)
        RETURN vpce.vpc_endpoint_id, subnet.subnetid
        """,
    )
    actual = {(r["vpce.vpc_endpoint_id"], r["subnet.subnetid"]) for r in result}

    assert actual == expected_rels


def test_load_vpc_endpoint_security_group_relationships(neo4j_session):
    """Test that interface and gateway load balancer VPC endpoints are linked to security groups"""
    # Create test security groups
    neo4j_session.run(
        """
        MERGE (sg1:EC2SecurityGroup{id: 'sg-12345'})
        ON CREATE SET sg1.firstseen = timestamp()
        SET sg1.lastupdated = $update_tag

        MERGE (sg2:EC2SecurityGroup{id: 'sg-gwlb'})
        ON CREATE SET sg2.firstseen = timestamp()
        SET sg2.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_security_group_relationships(
        neo4j_session,
        transformed_data,
        TEST_UPDATE_TAG,
    )

    # Interface and GatewayLoadBalancer endpoints should have security group relationships
    expected_rels = {
        ("vpce-1234567890abcdef0", "sg-12345"),
        ("vpce-gwlb456", "sg-gwlb"),
    }

    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint)-[:MEMBER_OF_SECURITY_GROUP]->(sg:EC2SecurityGroup)
        RETURN vpce.vpc_endpoint_id, sg.id
        """,
    )
    actual = {(r["vpce.vpc_endpoint_id"], r["sg.id"]) for r in result}

    assert actual == expected_rels


def test_load_vpc_endpoint_route_table_relationships(neo4j_session):
    """Test that gateway VPC endpoints are linked to route tables"""
    # Create test route tables
    neo4j_session.run(
        """
        MERGE (rtb1:AWSRouteTable{id: 'rtb-12345'})
        ON CREATE SET rtb1.firstseen = timestamp()
        SET rtb1.lastupdated = $update_tag

        MERGE (rtb2:AWSRouteTable{id: 'rtb-67890'})
        ON CREATE SET rtb2.firstseen = timestamp()
        SET rtb2.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_route_table_relationships(
        neo4j_session,
        transformed_data,
        TEST_UPDATE_TAG,
    )

    # Only Gateway endpoint should have route table relationships
    expected_rels = {
        ("vpce-gateway123", "rtb-12345"),
        ("vpce-gateway123", "rtb-67890"),
    }

    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint)-[:ROUTES_THROUGH]->(rtb:AWSRouteTable)
        RETURN vpce.vpc_endpoint_id, rtb.id
        """,
    )
    actual = {(r["vpce.vpc_endpoint_id"], r["rtb.id"]) for r in result}

    assert actual == expected_rels


def test_vpc_endpoint_properties(neo4j_session):
    """Test that VPC endpoint properties are stored correctly"""
    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS, TEST_REGION)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Check Interface endpoint properties
    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-1234567890abcdef0'})
        RETURN
            vpce.service_name,
            vpce.private_dns_enabled,
            vpce.requester_managed,
            vpce.ip_address_type
        """,
    )
    record = result.single()

    assert record["vpce.service_name"] == "com.amazonaws.us-east-1.s3"
    assert record["vpce.private_dns_enabled"] is True
    assert record["vpce.requester_managed"] is False
    assert record["vpce.ip_address_type"] == "ipv4"

    # Check Gateway endpoint properties
    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-gateway123'})
        RETURN
            vpce.service_name,
            vpce.vpc_endpoint_type
        """,
    )
    record = result.single()

    assert record["vpce.service_name"] == "com.amazonaws.us-east-1.dynamodb"
    assert record["vpce.vpc_endpoint_type"] == "Gateway"


@patch.object(
    cartography.intel.aws.ec2.vpc_endpoint,
    "get_vpc_endpoints",
    return_value=DESCRIBE_VPC_ENDPOINTS,
)
def test_sync_vpc_endpoints(mock_get_vpc_endpoints, neo4j_session):
    """
    Test that VPC endpoints sync correctly and create proper nodes and relationships
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_vpc_endpoints(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert VPC endpoints exist with correct types
    assert check_nodes(neo4j_session, "AWSVpcEndpoint", ["vpc_endpoint_id", "vpc_endpoint_type"]) == {
        ("vpce-1234567890abcdef0", "Interface"),
        ("vpce-gateway123", "Gateway"),
        ("vpce-gwlb456", "GatewayLoadBalancer"),
    }

    # Assert VPC endpoints are connected to AWS account
    assert check_rels(
        neo4j_session,
        "AWSVpcEndpoint",
        "vpc_endpoint_id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("vpce-1234567890abcdef0", TEST_ACCOUNT_ID),
        ("vpce-gateway123", TEST_ACCOUNT_ID),
        ("vpce-gwlb456", TEST_ACCOUNT_ID),
    }
