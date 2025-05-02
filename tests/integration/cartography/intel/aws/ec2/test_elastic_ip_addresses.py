import cartography.intel.aws.ec2.elastic_ip_addresses
import tests.data.aws.ec2.elastic_ip_addresses

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_elastic_ip_addresses(neo4j_session, *args):
    """
    Ensure that expected ip addresses get loaded with their key fields.
    """
    data = tests.data.aws.ec2.elastic_ip_addresses.GET_ELASTIC_IP_ADDRESSES
    cartography.intel.aws.ec2.elastic_ip_addresses.load_elastic_ip_addresses(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "192.168.1.1",
            "eipassoc-00000000000000000",
            "192.168.1.1",
            "192.168.1.2",
            "eni-00000000000000000",
            "000000000000",
            "us-east-1",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ElasticIPAddress)
        RETURN n.id, n.association_id, n.public_ip, n.private_ip_address,
        n.network_interface_id, n.network_interface_owner_id,
        n.region
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.association_id"],
            n["n.public_ip"],
            n["n.private_ip_address"],
            n["n.network_interface_id"],
            n["n.network_interface_owner_id"],
            n["n.region"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
