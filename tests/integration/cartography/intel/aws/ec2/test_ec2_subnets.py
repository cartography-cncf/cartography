import cartography.intel.aws.ec2
import tests.data.aws.ec2.subnets
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


def test_load_subnets(neo4j_session):
    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Assert that we create EC2Subnet nodes and correctly include their subnetid field
    assert check_nodes(neo4j_session, 'EC2Subnet', ['subnetid', 'subnet_arn']) == {
        (
            'subnet-020b2f3928f190ce8',
            'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-020b2f3928f190ce8',
        ),
        (
            'subnet-0773409557644dca4',
            'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0773409557644dca4',
        ),
        (
            'subnet-0fa9c8fa7cb241479',
            'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0fa9c8fa7cb241479',
        ),
    }


def test_load_subnet_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('000000000000', 'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0fa9c8fa7cb241479'),
        ('000000000000', 'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-020b2f3928f190ce8'),
        ('000000000000', 'arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0773409557644dca4'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EC2Subnet) RETURN n1.id, n2.subnet_arn;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.subnet_arn']) for r in result
    }

    assert actual == expected_nodes
