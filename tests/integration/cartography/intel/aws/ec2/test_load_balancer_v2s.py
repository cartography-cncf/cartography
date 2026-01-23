from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.load_balancer_v2s
from cartography.intel.aws.ec2.load_balancer_v2s import sync_load_balancer_v2s
from tests.data.aws.ec2.load_balancer_v2s import GET_LOAD_BALANCER_V2_DATA
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_test_subnets_security_groups_and_instances(neo4j_session):
    """Create test subnets, security groups, and EC2 instances for relationship testing."""
    # Create subnets
    for subnet_id in ["subnet-11111111", "subnet-22222222", "subnet-33333333"]:
        neo4j_session.run(
            """
            MERGE (s:EC2Subnet{subnetid: $subnet_id})
            SET s.lastupdated = $update_tag
            """,
            subnet_id=subnet_id,
            update_tag=TEST_UPDATE_TAG,
        )
    # Create security groups
    for sg_id in ["sg-12345678", "sg-87654321"]:
        neo4j_session.run(
            """
            MERGE (sg:EC2SecurityGroup{groupid: $sg_id})
            SET sg.lastupdated = $update_tag
            """,
            sg_id=sg_id,
            update_tag=TEST_UPDATE_TAG,
        )
    # Create EC2 instances
    for instance_id in ["i-1234567890abcdef0", "i-0987654321fedcba0"]:
        neo4j_session.run(
            """
            MERGE (i:EC2Instance{instanceid: $instance_id})
            SET i.lastupdated = $update_tag
            """,
            instance_id=instance_id,
            update_tag=TEST_UPDATE_TAG,
        )


@patch.object(
    cartography.intel.aws.ec2.load_balancer_v2s,
    "get_loadbalancer_v2_data",
    return_value=GET_LOAD_BALANCER_V2_DATA,
)
def test_sync_load_balancer_v2s(mock_get_loadbalancer_v2_data, neo4j_session):
    """
    Ensure that LoadBalancerV2 and ELBV2Listener are synced correctly with relationships.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_test_subnets_security_groups_and_instances(neo4j_session)

    # Act
    sync_load_balancer_v2s(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - LoadBalancerV2 nodes exist
    assert check_nodes(
        neo4j_session,
        "LoadBalancerV2",
        ["id", "name", "type", "scheme"],
    ) == {
        (
            "test-alb-1234567890.us-east-1.elb.amazonaws.com",
            "test-alb",
            "application",
            "internet-facing",
        ),
        (
            "test-nlb-abcdef0123.us-east-1.elb.amazonaws.com",
            "test-nlb",
            "network",
            "internal",
        ),
    }

    # Assert - Relationships (AWSAccount)-[RESOURCE]->(LoadBalancerV2)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "LoadBalancerV2",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "test-alb-1234567890.us-east-1.elb.amazonaws.com"),
        (TEST_ACCOUNT_ID, "test-nlb-abcdef0123.us-east-1.elb.amazonaws.com"),
    }

    # Assert - ELBV2Listener nodes exist
    assert check_nodes(
        neo4j_session,
        "ELBV2Listener",
        ["id", "port", "protocol"],
    ) == {
        (
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/abcdef1234567890",
            443,
            "HTTPS",
        ),
        (
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/1234567890abcdef",
            80,
            "HTTP",
        ),
        (
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/net/test-nlb/abcdef0123456789/fedcba9876543210",
            443,
            "TLS",
        ),
    }

    # Assert - Relationships (LoadBalancerV2)-[ELBV2_LISTENER]->(ELBV2Listener)
    assert check_rels(
        neo4j_session,
        "LoadBalancerV2",
        "id",
        "ELBV2Listener",
        "id",
        "ELBV2_LISTENER",
        rel_direction_right=True,
    ) == {
        (
            "test-alb-1234567890.us-east-1.elb.amazonaws.com",
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/abcdef1234567890",
        ),
        (
            "test-alb-1234567890.us-east-1.elb.amazonaws.com",
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/1234567890abcdef",
        ),
        (
            "test-nlb-abcdef0123.us-east-1.elb.amazonaws.com",
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/net/test-nlb/abcdef0123456789/fedcba9876543210",
        ),
    }

    # Assert - Relationships (LoadBalancerV2)-[SUBNET]->(EC2Subnet)
    assert check_rels(
        neo4j_session,
        "LoadBalancerV2",
        "id",
        "EC2Subnet",
        "subnetid",
        "SUBNET",
        rel_direction_right=True,
    ) == {
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "subnet-11111111"),
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "subnet-22222222"),
        ("test-nlb-abcdef0123.us-east-1.elb.amazonaws.com", "subnet-33333333"),
    }

    # Assert - Relationships (LoadBalancerV2)-[MEMBER_OF_EC2_SECURITY_GROUP]->(EC2SecurityGroup)
    # Only ALBs have security groups, not NLBs
    assert check_rels(
        neo4j_session,
        "LoadBalancerV2",
        "id",
        "EC2SecurityGroup",
        "groupid",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "sg-12345678"),
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "sg-87654321"),
    }

    # Assert - Relationships (LoadBalancerV2)-[EXPOSE]->(EC2Instance)
    # Only for target groups with target type = instance
    assert check_rels(
        neo4j_session,
        "LoadBalancerV2",
        "id",
        "EC2Instance",
        "instanceid",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "i-1234567890abcdef0"),
        ("test-alb-1234567890.us-east-1.elb.amazonaws.com", "i-0987654321fedcba0"),
    }
