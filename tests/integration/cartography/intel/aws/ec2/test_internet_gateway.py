import cartography.intel.aws.ec2
import tests.data.aws.ec2.internet_gateway
import tests.integration.cartography.intel.aws.common

TEST_ACCOUNT_ID = "012345678912"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_internet_gateways(neo4j_session):
    data = tests.data.aws.ec2.internet_gateway.DESCRIBE_GATEWAYS
    cartography.intel.aws.ec2.internet_gateways.load_internet_gateways(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "igw-1234XXX",
        "igw-7e3a7c18",
        "igw-f1c81494",
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSInternetGateway) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_internet_gateway_relationships(neo4j_session):
    tests.integration.cartography.intel.aws.common.create_test_account(
        neo4j_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.internet_gateway.DESCRIBE_GATEWAYS
    cartography.intel.aws.ec2.internet_gateways.load_internet_gateways(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_ACCOUNT_ID, "igw-1234XXX"),
        (TEST_ACCOUNT_ID, "igw-7e3a7c18"),
        (TEST_ACCOUNT_ID, "igw-f1c81494"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSInternetGateway)<-[:RESOURCE]-(n2:AWSAccount) RETURN n1.id, n2.id;
        """,
    )
    actual = {(n["n2.id"], n["n1.id"]) for n in result}

    assert actual == expected
