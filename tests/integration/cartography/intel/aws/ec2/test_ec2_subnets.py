from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import cartography.intel.aws.ec2.subnets
import tests.data.aws.ec2.subnets
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.network_interfaces import sync_network_interfaces
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.ec2.network_interfaces import DESCRIBE_NETWORK_INTERFACES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

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


@patch.object(
    cartography.intel.aws.ec2.subnets,
    "get_subnet_data",
    return_value=tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS,
)
def test_sync_subnets(mock_get_subnets, neo4j_session):

    # Arrange
    boto3_session = MagicMock()
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n
        """,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create VPC nodes that the subnets reference
    neo4j_session.run(
        """
        MERGE (vpc1:AWSVpc{id: "vpc-025873e026b9e8ee6"})
        ON CREATE SET vpc1.firstseen = timestamp()
        SET vpc1.lastupdated = $aws_update_tag
        """,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (vpc2:AWSVpc{id: "vpc-05326141848d1c681"})
        ON CREATE SET vpc2.firstseen = timestamp()
        SET vpc2.lastupdated = $aws_update_tag
        """,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Act - Use the sync function instead of calling load directly
    cartography.intel.aws.ec2.subnets.sync_subnets(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Test outcomes: verify data is written to the graph as expected
    # Check that EC2Subnet nodes are created with correct properties
    expected_subnet_nodes = {
        ("subnet-020b2f3928f190ce8", "10.1.2.0/24"),
        ("subnet-0773409557644dca4", "10.1.1.0/24"),
        ("subnet-0fa9c8fa7cb241479", "10.2.1.0/24"),
    }
    assert (
        check_nodes(neo4j_session, "EC2Subnet", ["subnetid", "cidr_block"])
        == expected_subnet_nodes
    )

    # Check that subnets are connected to AWS account
    expected_account_rels = {
        (TEST_ACCOUNT_ID, "subnet-020b2f3928f190ce8"),
        (TEST_ACCOUNT_ID, "subnet-0773409557644dca4"),
        (TEST_ACCOUNT_ID, "subnet-0fa9c8fa7cb241479"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "EC2Subnet",
            "subnetid",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_rels
    )

    # Check that subnets are connected to their VPCs
    expected_vpc_rels = {
        ("subnet-020b2f3928f190ce8", "vpc-025873e026b9e8ee6"),
        ("subnet-0773409557644dca4", "vpc-025873e026b9e8ee6"),
        ("subnet-0fa9c8fa7cb241479", "vpc-05326141848d1c681"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EC2Subnet",
            "subnetid",
            "AWSVpc",
            "id",
            "MEMBER_OF_AWS_VPC",
            rel_direction_right=True,
        )
        == expected_vpc_rels
    )

    # Verify subnet properties are set correctly using check_nodes()
    all_subnet_props = check_nodes(
        neo4j_session,
        "EC2Subnet",
        ["subnetid", "availability_zone", "state", "available_ip_address_count"],
    )
    assert (
        "subnet-0773409557644dca4",
        "eu-north-1a",
        "available",
        251,
    ) in all_subnet_props
