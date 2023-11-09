from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.network_interfaces
from cartography.intel.aws.ec2.network_interfaces import sync_network_interfaces
from tests.data.aws.ec2.network_interfaces import DESCRIBE_NETWORK_INTERFACES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.network_interfaces,
    'get_network_interface_data',
    return_value=DESCRIBE_NETWORK_INTERFACES,
)
def test_load_network_interfaces(mock_get_network_interfaces, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_network_interfaces(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert NetworkInterfaces were created
    assert check_nodes(neo4j_session, 'NetworkInterface', ['id']) == {
        ("eni-0e106a07c15ff7d14",),
        ("eni-0d9877f559c240362",),
        ("eni-04b4289e1be7634e4",),
    }

    # Assert EC2PrivateIps were created
    assert check_nodes(neo4j_session, 'EC2PrivateIp', ['id']) == {
        ("eni-0e106a07c15ff7d14:10.0.4.180",),
        ("eni-0d9877f559c240362:10.0.4.96",),
        ("eni-04b4289e1be7634e4:10.0.4.5",),
        ("eni-04b4289e1be7634e4:10.0.4.12",),
    }

    # Assert NetworkInterface to PrivateIp rels exist
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2PrivateIp',
        'id',
        'PRIVATE_IP_ADDRESS',
        rel_direction_right=True,
    ) == {
        ('eni-0e106a07c15ff7d14', 'eni-0e106a07c15ff7d14:10.0.4.180'),
        ('eni-0d9877f559c240362', 'eni-0d9877f559c240362:10.0.4.96'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.5'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.12'),
    }

    # Assert NetworkInterface to AWSAccount rels exist
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('eni-0e106a07c15ff7d14', TEST_ACCOUNT_ID),
        ('eni-0d9877f559c240362', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
    }

    # Assert NetworkInterface to Subnet rels exist
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2Subnet',
        'id',
        'PART_OF_SUBNET',
        rel_direction_right=True,
    ) == {
        ('eni-04b4289e1be7634e4', 'subnet-0fa10e76eeb24dbe7'),
        ('eni-0d9877f559c240362', 'subnet-0fa10e76eeb24dbe7'),
        ('eni-0e106a07c15ff7d14', 'subnet-0fa10e76eeb24dbe7'),
    }

    # Assert NetworkInterface to security group rels exist
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2SecurityGroup',
        'id',
        'MEMBER_OF_EC2_SECURITY_GROUP',
        rel_direction_right=True,
    ) == {
        ('eni-04b4289e1be7634e4', 'sg-0e866e64db0c84705'),
        ('eni-0d9877f559c240362', 'sg-0e866e64db0c84705'),
        ('eni-0e106a07c15ff7d14', 'sg-0e866e64db0c84705'),
    }
