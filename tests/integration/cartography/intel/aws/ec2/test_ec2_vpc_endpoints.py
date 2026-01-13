from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.vpc_endpoint
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_route_tables
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_security_groups
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoint_subnets
from cartography.intel.aws.ec2.vpc_endpoint import load_vpc_endpoints
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
    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert that VPC endpoint nodes are created
    assert check_nodes(
        neo4j_session,
        "AWSVpcEndpoint",
        ["vpc_endpoint_id", "vpc_endpoint_type", "state"],
    ) == {
        ("vpce-1234567890abcdef0", "Interface", "available"),
        ("vpce-gateway123", "Gateway", "available"),
        ("vpce-gwlb456", "GatewayLoadBalancer", "available"),
    }


def test_load_vpc_endpoint_to_account_relationship(neo4j_session):
    """Test that VPC endpoints are linked to AWS accounts"""
    # Create test AWS account
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
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

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
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
    # Create test account (required for schema-based loading)
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_subnets(
        neo4j_session,
        transformed_data.subnet_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
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
    # Create test account (required for schema-based loading)
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_security_groups(
        neo4j_session,
        transformed_data.security_group_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
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
    # Create test account (required for schema-based loading)
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_vpc_endpoint_route_tables(
        neo4j_session,
        transformed_data.route_table_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
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
    transformed_data = transform_vpc_endpoint_data(DESCRIBE_VPC_ENDPOINTS)
    load_vpc_endpoints(
        neo4j_session,
        transformed_data.vpc_endpoint_list,
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
    assert check_nodes(
        neo4j_session, "AWSVpcEndpoint", ["vpc_endpoint_id", "vpc_endpoint_type"]
    ) == {
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


@patch.object(
    cartography.intel.aws.ec2.vpc_endpoint,
    "get_vpc_endpoints",
    return_value=DESCRIBE_VPC_ENDPOINTS,
)
def test_cleanup_vpc_endpoints_removes_stale_nodes(
    mock_get_vpc_endpoints, neo4j_session
):
    """
    Test that cleanup removes stale VPC endpoint nodes
    """
    OLD_UPDATE_TAG = 111111
    NEW_UPDATE_TAG = 222222

    # Arrange - Create account and stale VPC endpoint
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, NEW_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (account:AWSAccount {id: $AccountId})
        CREATE (stale:AWSVpcEndpoint {
            id: 'vpce-STALE-OLD',
            vpc_endpoint_id: 'vpce-STALE-OLD',
            vpc_id: 'vpc-12345678',
            service_name: 'com.amazonaws.us-east-1.dynamodb',
            vpc_endpoint_type: 'Gateway',
            state: 'deleted',
            region: $Region,
            lastupdated: $OldTag,
            _module_name: 'cartography:aws',
            _module_version: '0.0.0'
        })
        CREATE (account)-[:RESOURCE {
            lastupdated: $OldTag,
            _module_name: 'cartography:aws',
            _module_version: '0.0.0',
            firstseen: timestamp()
        }]->(stale)
        """,
        AccountId=TEST_ACCOUNT_ID,
        Region=TEST_REGION,
        OldTag=OLD_UPDATE_TAG,
    )

    # Verify stale node exists
    result = neo4j_session.run(
        "MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-STALE-OLD'}) RETURN count(vpce) as count"
    )
    assert result.single()["count"] == 1

    # Act - Run sync with new update tag
    boto3_session = MagicMock()
    sync_vpc_endpoints(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        NEW_UPDATE_TAG,
        {"UPDATE_TAG": NEW_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Stale node should be removed
    result = neo4j_session.run(
        "MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-STALE-OLD'}) RETURN count(vpce) as count"
    )
    assert result.single()["count"] == 0

    # Assert - Fresh nodes should still exist
    assert check_nodes(neo4j_session, "AWSVpcEndpoint", ["vpc_endpoint_id"]) == {
        ("vpce-1234567890abcdef0",),
        ("vpce-gateway123",),
        ("vpce-gwlb456",),
    }


@patch.object(
    cartography.intel.aws.ec2.vpc_endpoint,
    "get_vpc_endpoints",
    return_value=DESCRIBE_VPC_ENDPOINTS,
)
def test_cleanup_vpc_endpoints_removes_stale_manual_relationships(
    mock_get_vpc_endpoints, neo4j_session
):
    """
    Test that cleanup removes stale manual relationships (ROUTES_THROUGH, USES_SUBNET, MEMBER_OF_SECURITY_GROUP)
    """
    OLD_UPDATE_TAG = 111111
    NEW_UPDATE_TAG = 222222

    # Arrange - Create account, VPC endpoint, and related resources
    # Note: Stub nodes must have RESOURCE relationship to account for schema-based cleanup to work
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, NEW_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (account:AWSAccount {id: $AccountId})

        MERGE (subnet:EC2Subnet {subnetid: 'subnet-stale'})
        ON CREATE SET subnet.firstseen = timestamp()
        SET subnet.lastupdated = $NewTag
        MERGE (account)-[:RESOURCE {lastupdated: $NewTag}]->(subnet)

        MERGE (sg:EC2SecurityGroup {id: 'sg-stale'})
        ON CREATE SET sg.firstseen = timestamp()
        SET sg.lastupdated = $NewTag
        MERGE (account)-[:RESOURCE {lastupdated: $NewTag}]->(sg)

        MERGE (rtb:AWSRouteTable {id: 'rtb-stale'})
        ON CREATE SET rtb.firstseen = timestamp()
        SET rtb.lastupdated = $NewTag
        MERGE (account)-[:RESOURCE {lastupdated: $NewTag}]->(rtb)
        """,
        AccountId=TEST_ACCOUNT_ID,
        NewTag=NEW_UPDATE_TAG,
    )

    # Act - First sync creates endpoints with relationships
    boto3_session = MagicMock()
    sync_vpc_endpoints(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        NEW_UPDATE_TAG,
        {"UPDATE_TAG": NEW_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Create stale manual relationships
    neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-1234567890abcdef0'})
        MATCH (subnet:EC2Subnet {subnetid: 'subnet-stale'})
        MATCH (sg:EC2SecurityGroup {id: 'sg-stale'})
        MATCH (rtb:AWSRouteTable {id: 'rtb-stale'})
        CREATE (vpce)-[:USES_SUBNET {lastupdated: $OldTag, _module_name: 'cartography:aws', _module_version: '0.0.0', firstseen: timestamp()}]->(subnet)
        CREATE (vpce)-[:MEMBER_OF_SECURITY_GROUP {lastupdated: $OldTag, _module_name: 'cartography:aws', _module_version: '0.0.0', firstseen: timestamp()}]->(sg)
        CREATE (vpce)-[:ROUTES_THROUGH {lastupdated: $OldTag, _module_name: 'cartography:aws', _module_version: '0.0.0', firstseen: timestamp()}]->(rtb)
        """,
        OldTag=OLD_UPDATE_TAG,
    )

    # Verify stale relationships exist
    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-1234567890abcdef0'})-[r:USES_SUBNET|MEMBER_OF_SECURITY_GROUP|ROUTES_THROUGH]->()
        WHERE r.lastupdated = $OldTag
        RETURN count(r) as count
        """,
        OldTag=OLD_UPDATE_TAG,
    )
    assert result.single()["count"] == 3

    # Act - Run sync again with new update tag
    NEWER_UPDATE_TAG = 333333
    sync_vpc_endpoints(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        NEWER_UPDATE_TAG,
        {"UPDATE_TAG": NEWER_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Stale manual relationships should be removed
    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-1234567890abcdef0'})-[r:USES_SUBNET|MEMBER_OF_SECURITY_GROUP|ROUTES_THROUGH]->()
        WHERE r.lastupdated = $OldTag
        RETURN count(r) as count
        """,
        OldTag=OLD_UPDATE_TAG,
    )
    assert result.single()["count"] == 0

    # Assert - Fresh relationships should still exist (from test data)
    result = neo4j_session.run(
        """
        MATCH (vpce:AWSVpcEndpoint {vpc_endpoint_id: 'vpce-1234567890abcdef0'})-[r:USES_SUBNET|MEMBER_OF_SECURITY_GROUP]->()
        WHERE r.lastupdated = $NewTag
        RETURN count(r) as count
        """,
        NewTag=NEWER_UPDATE_TAG,
    )
    # Interface endpoint should have 2 subnets + 1 security group = 3 relationships
    assert result.single()["count"] == 3
