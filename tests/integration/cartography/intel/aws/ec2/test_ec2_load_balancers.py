import cartography.intel.aws.ec2
import tests.data.aws.ec2.load_balancers

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
        SET aws.lastupdated = $aws_update_tag

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

        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        load_balancer_id=load_balancer_id,
        ec2_instance_id=ec2_instance_id,
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

    # verify the db has (load_balancer_id)-[r:EXPOSE]->(instance)
    nodes = neo4j_session.run(
        """
        MATCH (elbv2:LoadBalancerV2{id: $ID})-[r:EXPOSE]->(instance:EC2Instance{instanceid: $INSTANCE_ID})
        RETURN elbv2.id, instance.instanceid
        """,
        ID=load_balancer_id,
        INSTANCE_ID=ec2_instance_id,
    )

    expected_nodes = {
        (
            load_balancer_id,
            ec2_instance_id,
        ),
    }
    actual_nodes = {
        (
            n["elbv2.id"],
            n["instance.instanceid"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_load_balancer_v2_subnets(neo4j_session, *args):
    # an elbv2 must exist or nothing will match.
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

    az_data = [
        {"SubnetId": "mysubnetIdA"},
        {"SubnetId": "mysubnetIdB"},
    ]
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2_subnets(
        neo4j_session,
        load_balancer_id,
        az_data,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "mysubnetIdA",
            TEST_REGION,
            TEST_UPDATE_TAG,
        ),
        (
            "mysubnetIdB",
            TEST_REGION,
            TEST_UPDATE_TAG,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (subnet:EC2Subnet) return subnet.subnetid, subnet.region, subnet.lastupdated
        """,
    )
    actual_nodes = {
        (
            n["subnet.subnetid"],
            n["subnet.region"],
            n["subnet.lastupdated"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
