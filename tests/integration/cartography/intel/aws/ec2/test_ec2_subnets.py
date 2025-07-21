from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import tests.data.aws.ec2.subnets
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.network_interfaces import sync_network_interfaces
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.ec2.network_interfaces import DESCRIBE_NETWORK_INTERFACES
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
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
    assert check_nodes(neo4j_session, "EC2Subnet", ["subnetid", "subnet_arn"]) == {
        (
            "subnet-020b2f3928f190ce8",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-020b2f3928f190ce8",
        ),
        (
            "subnet-0773409557644dca4",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0773409557644dca4",
        ),
        (
            "subnet-0fa9c8fa7cb241479",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0fa9c8fa7cb241479",
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
        (
            "000000000000",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0fa9c8fa7cb241479",
        ),
        (
            "000000000000",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-020b2f3928f190ce8",
        ),
        (
            "000000000000",
            "arn:aws:ec2:eu-north-1:000000000000:subnet/subnet-0773409557644dca4",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EC2Subnet) RETURN n1.id, n2.subnet_arn;
        """,
    )
    actual = {(r["n1.id"], r["n2.subnet_arn"]) for r in result}

    assert actual == expected_nodes


@patch.object(
    cartography.intel.aws.ec2.network_interfaces,
    "get_network_interface_data",
    return_value=DESCRIBE_NETWORK_INTERFACES,
)
@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
def test_detect_inconsistent_subnet_property_naming(
    mock_get_instances, mock_get_network_interfaces, neo4j_session
):
    """
    Test to detect inconsistent property naming in EC2Subnet nodes.

    This test should FAIL when there are EC2Subnet nodes with inconsistent
    property naming (some with 'subnetid', others with 'subnet_id').
    The test should PASS when all nodes use consistent property naming.
    """
    boto3_session = MagicMock()

    # Arrange and Act: create all nodes in cartography that use subnetid and subnet_id
    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    sync_network_interfaces(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: Check for nodes with subnetid but no subnet_id
    result_subnetid_only = neo4j_session.run(
        """
        MATCH (s:EC2Subnet)
        WHERE s.subnetid IS NOT NULL AND s.subnet_id IS NULL
        RETURN count(s) as count
        """
    )
    subnetid_only_count = result_subnetid_only.single()["count"]

    # Check for nodes with subnet_id but no subnetid
    result_subnet_id_only = neo4j_session.run(
        """
        MATCH (s:EC2Subnet)
        WHERE s.subnet_id IS NOT NULL AND s.subnetid IS NULL
        RETURN count(s) as count
        """
    )
    subnet_id_only_count = result_subnet_id_only.single()["count"]

    # The test should FAIL if we have both types of nodes (inconsistent state)
    # This indicates the bug exists
    assert subnetid_only_count == 0 or subnet_id_only_count == 0, (
        f"Found inconsistent EC2Subnet property naming: "
        f"{subnetid_only_count} nodes with 'subnetid' only, "
        f"{subnet_id_only_count} nodes with 'subnet_id' only. "
        f"All nodes should use consistent property naming."
    )
