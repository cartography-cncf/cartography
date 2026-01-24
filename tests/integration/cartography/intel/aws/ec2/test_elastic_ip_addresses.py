from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.elastic_ip_addresses
from cartography.intel.aws.ec2.elastic_ip_addresses import sync_elastic_ip_addresses
from tests.data.aws.ec2.elastic_ip_addresses import GET_ELASTIC_IP_ADDRESSES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.elastic_ip_addresses,
    "get_elastic_ip_addresses",
    return_value=GET_ELASTIC_IP_ADDRESSES,
)
def test_sync_elastic_ip_addresses(mock_get_elastic_ip_addresses, neo4j_session):
    """
    Ensure that elastic IP addresses are synced correctly with their nodes and relationships.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_elastic_ip_addresses(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Nodes
    assert check_nodes(
        neo4j_session,
        "ElasticIPAddress",
        ["id", "public_ip", "private_ip_address", "region"],
    ) == {
        ("192.168.1.1", "192.168.1.1", "192.168.1.2", "us-east-1"),
    }

    # Assert - Relationships (AWSAccount)-[RESOURCE]->(ElasticIPAddress)
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "ElasticIPAddress",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "192.168.1.1"),
    }
