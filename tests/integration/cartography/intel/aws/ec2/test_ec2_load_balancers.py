from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import tests.data.aws.ec2.load_balancers
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.load_balancers import sync_load_balancers
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.ec2.load_balancers import DESCRIBE_LOAD_BALANCERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_load_balancer_v2s(neo4j_session, *args):
    load_balancer_data = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA
    ec2_instance_id = "i-0f76fade"
    sg_group_id = "sg-123456"
    sg_group_id_2 = "sg-234567"
    load_balancer_id = "myawesomeloadbalancer.amazonaws.com"

    # an ec2instance and AWSAccount must exist
    neo4j_session.run(
        """
        MERGE (ec2:EC2Instance{instanceid: $ec2_instance_id})
        ON CREATE SET ec2.firstseen = timestamp()
        SET ec2.lastupdated = $aws_update_tag

        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant

        MERGE (group:EC2SecurityGroup{groupid: $GROUP_ID_1})
        ON CREATE SET group.firstseen = timestamp()
        SET group.last_updated = $aws_update_tag

        MERGE (group2:EC2SecurityGroup{groupid: $GROUP_ID_2})
        ON CREATE SET group2.firstseen = timestamp()
        SET group2.last_updated = $aws_update_tag
        """,
        ec2_instance_id=ec2_instance_id,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
        GROUP_ID_1=sg_group_id,
        GROUP_ID_2=sg_group_id_2,
    )

    # Makes elbv2
    # (aa)-[r:RESOURCE]->(elbv2)
    # also makes
    # (elbv2)->[RESOURCE]->(EC2Subnet)
    # also makes (relationship only, won't create SG)
    # (elbv2)->[MEMBER_OF_SECURITY_GROUP]->(EC2SecurityGroup)
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        load_balancer_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # verify the db has (aa)-[r:RESOURCE]->(elbv2)-[r:ELBV2_LISTENER]->(l)
    nodes = neo4j_session.run(
        """
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
            -[r1:RESOURCE]->(elbv2:LoadBalancerV2{id: $ID})
            -[r2:ELBV2_LISTENER]->(l:ELBV2Listener{id: $LISTENER_ARN})
        RETURN aa.id, elbv2.id, l.id
        """,
        AWS_ACCOUNT_ID=TEST_ACCOUNT_ID,
        ID=load_balancer_id,
        LISTENER_ARN="arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
    )
    expected_nodes = {
        (
            TEST_ACCOUNT_ID,
            load_balancer_id,
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
        ),
    }
    actual_nodes = {
        (
            n["aa.id"],
            n["elbv2.id"],
            n["l.id"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_load_balancer_v2_listeners(neo4j_session, *args):
    # elbv2 must exist
    # creates ELBV2Listener
    # creates (elbv2)-[r:ELBV2_LISTENER]->(l)
    load_balancer_id = "asadfmyloadbalancerid"
    neo4j_session.run(
        """
        MERGE (elbv2:LoadBalancerV2{id: $ID})
        ON CREATE SET elbv2.firstseen = timestamp()
        SET elbv2.lastupdated = $aws_udpate_tag
        """,
        ID=load_balancer_id,
        aws_udpate_tag=TEST_UPDATE_TAG,
    )

    listener_data = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_LISTENERS
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2_listeners(
        neo4j_session,
        load_balancer_id,
        listener_data,
        TEST_UPDATE_TAG,
        TEST_ACCOUNT_ID,
    )

    # verify the db has (elbv2)-[r:ELBV2_LISTENER]->(l)
    nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:ELBV2_LISTENER]->(l:ELBV2Listener{id: $LISTENER_ARN})
        RETURN elbv2.id, l.id
        """,
        ID=load_balancer_id,
        LISTENER_ARN="arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
    )

    expected_nodes = {
        (
            load_balancer_id,
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
        ),
    }
    actual_nodes = {
        (
            n["elbv2.id"],
            n["l.id"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_load_balancer_v2_target_groups(neo4j_session, *args):
    load_balancer_id = "asadfmyloadbalancerid"
    ec2_instance_id = "i-0f76fade"
    private_ip_address = "10.0.0.1"
    lambda_arn = "arn:aws:lambda:us-east-1:000000000000:function:example"
    target_alb_arn = "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/target-alb/1234567890abcdef"
    target_alb_id = "target-alb.us-east-1.elb.amazonaws.com"

    target_groups = tests.data.aws.ec2.load_balancers.TARGET_GROUPS

    # an elbv2, ec2instance, and AWSAccount must exist or nothing will match
    neo4j_session.run(
        """
        MERGE (elbv2:LoadBalancerV2{id: $load_balancer_id})
        ON CREATE SET elbv2.firstseen = timestamp()
        SET elbv2.lastupdated = $aws_update_tag

        MERGE (ec2:EC2Instance{instanceid: $ec2_instance_id})
        ON CREATE SET ec2.firstseen = timestamp()
        SET ec2.lastupdated = $aws_update_tag

        MERGE (private_ip:EC2PrivateIp{private_ip_address: $private_ip_address})
        ON CREATE SET private_ip.firstseen = timestamp()
        SET private_ip.lastupdated = $aws_update_tag

        MERGE (lambda_fn:AWSLambda{id: $lambda_arn})
        ON CREATE SET lambda_fn.firstseen = timestamp()
        SET lambda_fn.lastupdated = $aws_update_tag

        MERGE (target_alb:LoadBalancerV2{id: $target_alb_id, arn: $target_alb_arn})
        ON CREATE SET target_alb.firstseen = timestamp()
        SET target_alb.lastupdated = $aws_update_tag

        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
        """,
        load_balancer_id=load_balancer_id,
        ec2_instance_id=ec2_instance_id,
        private_ip_address=private_ip_address,
        lambda_arn=lambda_arn,
        target_alb_id=target_alb_id,
        target_alb_arn=target_alb_arn,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2_target_groups(
        neo4j_session,
        load_balancer_id,
        target_groups,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # verify the db has EXPOSE rels to instance, ip, and lambda targets
    instance_nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:EXPOSE]->(instance:EC2Instance{instanceid: $INSTANCE_ID})
        RETURN elbv2.id, instance.instanceid
        """,
        ID=load_balancer_id,
        INSTANCE_ID=ec2_instance_id,
    )

    ip_nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:EXPOSE]->(ip:EC2PrivateIp{private_ip_address: $private_ip_address})
        RETURN elbv2.id, ip.private_ip_address
        """,
        ID=load_balancer_id,
        private_ip_address=private_ip_address,
    )

    lambda_nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:EXPOSE]->(lambda_fn:AWSLambda{id: $lambda_arn})
        RETURN elbv2.id, lambda_fn.id
        """,
        ID=load_balancer_id,
        lambda_arn=lambda_arn,
    )

    alb_nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:EXPOSE]->(target_alb:LoadBalancerV2{arn: $target_alb_arn})
        RETURN elbv2.id, target_alb.id
        """,
        ID=load_balancer_id,
        target_alb_arn=target_alb_arn,
    )

    expected_nodes = {
        (
            load_balancer_id,
            ec2_instance_id,
        ),
        (
            load_balancer_id,
            private_ip_address,
        ),
        (
            load_balancer_id,
            lambda_arn,
        ),
        (
            load_balancer_id,
            target_alb_id,
        ),
    }
    actual_nodes = (
        {(n["elbv2.id"], n["instance.instanceid"]) for n in instance_nodes}
        | {(n["elbv2.id"], n["ip.private_ip_address"]) for n in ip_nodes}
        | {(n["elbv2.id"], n["lambda_fn.id"]) for n in lambda_nodes}
        | {(n["elbv2.id"], n["target_alb.id"]) for n in alb_nodes}
    )
    assert actual_nodes == expected_nodes


def test_load_load_balancer_v2_subnet_relationships(neo4j_session, *args):
    """Test that SUBNET relationships are created via the main loader when EC2Subnet nodes exist."""
    load_balancer_data = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA
    load_balancer_id = "myawesomeloadbalancer.amazonaws.com"

    # Create required nodes: AWSAccount, EC2SecurityGroups, EC2Subnets, EC2Instance
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant

        MERGE (ec2:EC2Instance{instanceid: $ec2_instance_id})
        ON CREATE SET ec2.firstseen = timestamp()
        SET ec2.lastupdated = $aws_update_tag

        MERGE (sg1:EC2SecurityGroup{groupid: $sg1})
        ON CREATE SET sg1.firstseen = timestamp()
        SET sg1.lastupdated = $aws_update_tag

        MERGE (sg2:EC2SecurityGroup{groupid: $sg2})
        ON CREATE SET sg2.firstseen = timestamp()
        SET sg2.lastupdated = $aws_update_tag

        MERGE (subnet:EC2Subnet{subnetid: $subnet_id})
        ON CREATE SET subnet.firstseen = timestamp(), subnet.id = $subnet_id
        SET subnet.region = $region, subnet.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
        ec2_instance_id="i-0f76fade",
        sg1="sg-123456",
        sg2="sg-234567",
        subnet_id="mysubnetIdA",
        region=TEST_REGION,
    )

    # Load the data via main loader
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        load_balancer_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Verify SUBNET relationship was created
    rels = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $lb_id})-[:SUBNET]->(subnet:EC2Subnet)
        RETURN elbv2.id, subnet.subnetid
        """,
        lb_id=load_balancer_id,
    )
    actual_rels = {(r["elbv2.id"], r["subnet.subnetid"]) for r in rels}
    expected_rels = {(load_balancer_id, "mysubnetIdA")}
    assert actual_rels == expected_rels


def _ensure_load_instances(neo4j_session):
    boto3_session = MagicMock()
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )


@patch.object(
    cartography.intel.aws.ec2.load_balancers,
    "get_loadbalancer_data",
    return_value=DESCRIBE_LOAD_BALANCERS["LoadBalancerDescriptions"],
)
@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
def test_sync_load_balancers(mock_get_instances, mock_get_loadbalancers, neo4j_session):
    """
    Ensure that load balancers and their listeners are loaded correctly
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_load_instances(neo4j_session)
    # Ugly ugly ugly hack so that the security group name is present in the test.
    # Currently the security group data in this test is only populated from describe-ec2-instances, which does not
    # return the security group name. The correct way would be to load in describe-security-groups, but that's a
    # lot of work for this test.
    neo4j_session.run(
        """
        MATCH (sg:EC2SecurityGroup{id: "SOME_GROUP_ID_2"})
        SET sg.name = "default"
        """,
    )

    # Act
    sync_load_balancers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert Load Balancers exist
    assert check_nodes(
        neo4j_session, "LoadBalancer", ["id", "name", "dnsname", "scheme"]
    ) == {
        (
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "test-lb-1",
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "internet-facing",
        ),
        (
            "test-lb-2-1234567890.us-east-1.elb.amazonaws.com",
            "test-lb-2",
            "test-lb-2-1234567890.us-east-1.elb.amazonaws.com",
            "internal",
        ),
    }

    # Assert Load Balancer Listeners exist
    assert check_nodes(
        neo4j_session,
        "ELBListener",
        ["id", "port", "protocol", "instance_port", "instance_protocol"],
    ) == {
        (
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com80HTTP",
            80,
            "HTTP",
            8080,
            "HTTP",
        ),
        (
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com443HTTPS",
            443,
            "HTTPS",
            8443,
            "HTTPS",
        ),
        (
            "test-lb-2-1234567890.us-east-1.elb.amazonaws.com8080TCP",
            8080,
            "TCP",
            8080,
            "TCP",
        ),
    }

    # Assert Load Balancer to Security Group relationships
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "EC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "THIS_IS_A_SG_ID"),
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "SOME_GROUP_ID_2"),
    }

    # Assert Load Balancers are attached to their Source Security Group
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "EC2SecurityGroup",
        "name",
        "SOURCE_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "default"),
    }

    # Assert Load Balancer to Instance relationships
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "EC2Instance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "i-01"),
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "i-02"),
        ("test-lb-2-1234567890.us-east-1.elb.amazonaws.com", "i-03"),
    }

    # Assert Load Balancer to Listener relationships
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "ELBListener",
        "id",
        "ELB_LISTENER",
        rel_direction_right=True,
    ) == {
        (
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com80HTTP",
        ),
        (
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "test-lb-1-1234567890.us-east-1.elb.amazonaws.com443HTTPS",
        ),
        (
            "test-lb-2-1234567890.us-east-1.elb.amazonaws.com",
            "test-lb-2-1234567890.us-east-1.elb.amazonaws.com8080TCP",
        ),
    }

    # Assert Load Balancer to AWS Account relationship
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com", "000000000000"),
        ("test-lb-2-1234567890.us-east-1.elb.amazonaws.com", "000000000000"),
    }

    # Assert ELBListener to AWS Account relationship
    assert check_rels(
        neo4j_session,
        "ELBListener",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com80HTTP", "000000000000"),
        ("test-lb-1-1234567890.us-east-1.elb.amazonaws.com443HTTPS", "000000000000"),
        ("test-lb-2-1234567890.us-east-1.elb.amazonaws.com8080TCP", "000000000000"),
    }


def test_load_balancer_v2s_skips_missing_dnsname(neo4j_session, *args):
    load_balancer_data = tests.data.aws.ec2.load_balancers.LOAD_BALANCER_DATA
    # Setup required nodes
    neo4j_session.run(
        """
        MERGE (ec2:EC2Instance{instanceid: $ec2_instance_id})
        ON CREATE SET ec2.firstseen = timestamp()
        SET ec2.lastupdated = $aws_update_tag

        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag, aws :Tenant

        MERGE (group:EC2SecurityGroup{groupid: $GROUP_ID_1})
        ON CREATE SET group.firstseen = timestamp()
        SET group.last_updated = $aws_update_tag

        MERGE (group2:EC2SecurityGroup{groupid: $GROUP_ID_2})
        ON CREATE SET group2.firstseen = timestamp()
        SET group2.last_updated = $aws_update_tag
        """,
        ec2_instance_id="i-0f76fade",
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
        GROUP_ID_1="sg-123456",
        GROUP_ID_2="sg-234567",
    )
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        load_balancer_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # The valid load balancer should be present
    valid_lb_id = ("myawesomeloadbalancer.amazonaws.com",)
    # The invalid load balancer should not be present
    invalid_lb_id = ("missingdnsnamelb",)
    actual = check_nodes(neo4j_session, "LoadBalancerV2", ["id"])
    assert valid_lb_id in actual
    assert invalid_lb_id not in actual
