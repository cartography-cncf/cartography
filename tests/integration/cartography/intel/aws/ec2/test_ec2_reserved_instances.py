from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.reserved_instances
from cartography.intel.aws.ec2.reserved_instances import sync_ec2_reserved_instances
from tests.data.aws.ec2.reserved_instances import DESCRIBE_RESERVED_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.reserved_instances,
    "get_reserved_instances",
    return_value=DESCRIBE_RESERVED_INSTANCES,
)
def test_sync_ec2_reserved_instances(mock_get_reserved_instances, neo4j_session):
    """
    Ensure that reserved instances are synced correctly with their nodes and relationships.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_ec2_reserved_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Nodes
    assert check_nodes(
        neo4j_session, "EC2ReservedInstance", ["id", "type", "state"]
    ) == {
        ("res-01", "t1.micro", "active"),
        ("res-02", "t2.large", "active"),
    }

    # Assert - Relationships (AWSAccount)-[RESOURCE]->(EC2ReservedInstance)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2ReservedInstance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "res-01"),
        (TEST_ACCOUNT_ID, "res-02"),
    }
