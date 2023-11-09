from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.ssm
import tests.data.aws.ec2.instances
import tests.data.aws.ssm
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_load_instances(neo4j_session):
    boto3_session = MagicMock()
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_load_instance_information(mock_get_instances, neo4j_session):
    # Arrange
    # load account and instances, to be able to test relationships
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_load_instances(neo4j_session)

    # Act
    data_list = cartography.intel.aws.ssm.transform_instance_information(tests.data.aws.ssm.INSTANCE_INFORMATION)
    cartography.intel.aws.ssm.load_instance_information(
        neo4j_session,
        data_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("i-01", 1647233782, 1647233908, 1647232108),
        ("i-02", 1647233782, 1647233908, 1647232108),
    }

    nodes = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: "000000000000"})-[:RESOURCE]->(n:SSMInstanceInformation)
        RETURN n.id,
               n.last_ping_date_time,
               n.last_association_execution_date,
               n.last_successful_association_execution_date
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.last_ping_date_time"],
            n["n.last_association_execution_date"],
            n["n.last_successful_association_execution_date"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-01"})-[:HAS_INFORMATION]->(n:SSMInstanceInformation)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-01"}

    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-02"})-[:HAS_INFORMATION]->(n:SSMInstanceInformation)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-02"}


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_load_instance_patches(mock_get_instances, neo4j_session):
    # Arrange: load account and instances, to be able to test relationships
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_load_instances(neo4j_session)

    # Act
    data_list = cartography.intel.aws.ssm.transform_instance_patches(tests.data.aws.ssm.INSTANCE_PATCHES)
    cartography.intel.aws.ssm.load_instance_patches(
        neo4j_session,
        data_list,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("i-01-test.x86_64:0:4.2.46-34.amzn2", 1636404678, ("CVE-2022-0000", "CVE-2022-0001")),
        ("i-02-test.x86_64:0:4.2.46-34.amzn2", 1636404678, ("CVE-2022-0000", "CVE-2022-0001")),
    }
    nodes = neo4j_session.run(
        """
        MATCH (:AWSAccount{id: "000000000000"})-[:RESOURCE]->(n:SSMInstancePatch)
        RETURN n.id,
               n.installed_time,
               n.cve_ids
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.installed_time"],
            tuple(n["n.cve_ids"]),
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-01"})-[:HAS_PATCH]->(n:SSMInstancePatch)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-01-test.x86_64:0:4.2.46-34.amzn2"}

    # Assert
    nodes = neo4j_session.run(
        """
        MATCH (:EC2Instance{id: "i-02"})-[:HAS_PATCH]->(n:SSMInstancePatch)
        RETURN n.id
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == {"i-02-test.x86_64:0:4.2.46-34.amzn2"}
