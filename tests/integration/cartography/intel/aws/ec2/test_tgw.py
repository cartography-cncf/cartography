import cartography.intel.aws.ec2
import tests.data.aws.ec2.tgw

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_load_transit_gateways(neo4j_session):
    data = tests.data.aws.ec2.tgw.TRANSIT_GATEWAYS
    cartography.intel.aws.ec2.tgw.load_transit_gateways(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:ec2:eu-west-1:000000000000:transit-gateway/tgw-0123456789abcdef0",
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSTransitGateway) RETURN n.arn;
        """,
    )
    actual_nodes = {n["n.arn"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_tgw_attachments(neo4j_session):
    data = (
        tests.data.aws.ec2.tgw.TRANSIT_GATEWAY_ATTACHMENTS
        + tests.data.aws.ec2.tgw.TGW_VPC_ATTACHMENTS
    )
    cartography.intel.aws.ec2.tgw.load_tgw_attachments(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "tgw-attach-aaaabbbbccccdef01",
    }

    nodes = neo4j_session.run(
        """
        MATCH (tgwa:AWSTransitGatewayAttachment)-[:ATTACHED_TO]->(tgw:AWSTransitGateway) RETURN tgwa.id;
        """,
    )
    actual_nodes = {n["tgwa.id"] for n in nodes}

    assert actual_nodes == expected_nodes
